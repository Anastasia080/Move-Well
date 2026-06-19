import cv2
import base64
import numpy as np
import os
from typing import List, Dict, Tuple, Optional
from collections import deque


class OpenPoseAnalyzer:
    """Анализатор с функцией сравнения с эталоном"""
    
    def __init__(self):
        proto_path = r"C:\movewell-backend\openpose\models\pose\coco\pose_deploy_linevec.prototxt"
        weights_path = r"C:\movewell-backend\openpose\models\pose\coco\pose_iter_440000.caffemodel"
        
        print(f"Loading OpenPose...")
        self.net = cv2.dnn.readNetFromCaffe(proto_path, weights_path)
        self.in_width = 368
        self.in_height = 368
        
        # Для сравнения с эталоном
        self.reference_poses = []  # Эталонные позы
        self.current_ref_frame = 0  # Текущий кадр эталона
        self.similarity_history = deque(maxlen=30)  # История сравнений
        
        print("OpenPose loaded!")
    
    def load_reference_video(self, video_path: str) -> bool:
        """
        Загружает эталонное видео и извлекает из него скелеты
        Возвращает True если успешно
        """
        print(f"Loading reference video: {video_path}")
        
        if not os.path.exists(video_path):
            print(f"ERROR: Reference video not found: {video_path}")
            return False
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("ERROR: Failed to open reference video")
            return False
        
        self.reference_poses = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Обрабатываем каждый 2-й кадр для скорости
            if frame_idx % 2 == 0:
                points = self._extract_points_from_frame(frame)
                
                # Сохраняем только если найдено достаточно точек
                if points and sum(1 for p in points if p is not None) >= 8:
                    self.reference_poses.append(points)
                    
                    # Показываем прогресс
                    if len(self.reference_poses) % 50 == 0:
                        print(f"  Processed {len(self.reference_poses)} reference poses...")
            
            frame_idx += 1
        
        cap.release()
        
        if len(self.reference_poses) > 0:
            print(f"SUCCESS: Loaded {len(self.reference_poses)} reference poses")
            self.current_ref_frame = 0
            return True
        else:
            print("ERROR: No poses extracted from reference video")
            return False
    
    def _extract_points_from_frame(self, frame: np.ndarray) -> List[Optional[Tuple[int, int]]]:
        """Извлекает ключевые точки из кадра"""
        h, w = frame.shape[:2]
        
        blob = cv2.dnn.blobFromImage(
            frame, 1.0/255.0, (self.in_width, self.in_height),
            (0, 0, 0), swapRB=False, crop=False
        )
        
        self.net.setInput(blob)
        output = self.net.forward()
        
        out_height, out_width = output.shape[2], output.shape[3]
        
        points = []
        for i in range(18):
            heatmap = output[0, i, :, :]
            _, confidence, _, max_loc = cv2.minMaxLoc(heatmap)
            
            if confidence > 0.1:
                x = int((max_loc[0] * w) / out_width)
                y = int((max_loc[1] * h) / out_height)
                points.append((x, y))
            else:
                points.append(None)
        
        return points
    
    def process_frame(self, image_base64: str, exercise: str) -> dict:
        """
        Основной метод: детекция скелета + сравнение с эталоном (если загружен)
        """
        try:
            # Декодируем изображение
            image_bytes = base64.b64decode(image_base64)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return self._error_response("Failed to decode image")
            
            h, w = frame.shape[:2]
            
            # Извлекаем точки
            points = self._extract_points_from_frame(frame)
            detected = sum(1 for p in points if p is not None)
            
            # Рисуем скелет пользователя
            result = frame.copy()
            self._draw_skeleton(result, points, color=(0, 255, 255))
            
            # Если есть эталон - сравниваем и рисуем эталонный скелет
            comparison_result = None
            if len(self.reference_poses) > 0 and detected >= 8:
                comparison_result = self._compare_with_reference(points)
                
                # Рисуем эталонный скелет другим цветом
                ref_points = self.reference_poses[self.current_ref_frame % len(self.reference_poses)]
                self._draw_skeleton(result, ref_points, color=(255, 0, 0), alpha=0.5)
                
                # Обновляем индекс эталонного кадра
                self.current_ref_frame += 1
                if self.current_ref_frame >= len(self.reference_poses):
                    self.current_ref_frame = 0  # Зацикливаем
            
            # Добавляем текст на изображение
            cv2.putText(result, f"Detected: {detected}/18", (10, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if comparison_result:
                similarity = comparison_result["similarity"]
                cv2.putText(result, f"Match: {similarity:.0f}%", (10, 55),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Цветовая индикация схожести
                if similarity > 80:
                    status_color = (0, 255, 0)
                    status_text = "EXCELLENT!"
                elif similarity > 60:
                    status_color = (0, 255, 255)
                    status_text = "GOOD"
                elif similarity > 40:
                    status_color = (0, 165, 255)
                    status_text = "TRY HARDER"
                else:
                    status_color = (0, 0, 255)
                    status_text = "KEEP TRYING"
                
                cv2.putText(result, status_text, (10, 85),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Кодируем результат
            _, buffer = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 85])
            skeleton_image = base64.b64encode(buffer).decode('utf-8')
            
            # Формируем ответ
            response = {
                "status": "good" if detected >= 10 else "needs_improvement" if detected >= 5 else "poor",
                "score": comparison_result["similarity"] if comparison_result else min(100, detected * 6),
                "feedback": comparison_result["feedback"] if comparison_result else f"Detected {detected} points",
                "joints_detected": detected,
                "errors": [],
                "skeleton_image": skeleton_image
            }
            
            if comparison_result:
                response["comparison"] = comparison_result
            
            return response
            
        except Exception as e:
            print(f"Error in process_frame: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(str(e))
    
    def _draw_skeleton(self, image: np.ndarray, points: List[Optional[Tuple[int, int]]], 
                       color=(0, 255, 255), alpha=1.0):
        """Рисует скелет на изображении"""
        skeleton_pairs = [
            (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),
            (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
            (1, 0), (0, 14), (14, 16), (0, 15), (15, 17)
        ]
        
        if alpha < 1.0:
            # Для полупрозрачного эталонного скелета
            overlay = image.copy()
            for pair in skeleton_pairs:
                if points[pair[0]] and points[pair[1]]:
                    cv2.line(overlay, points[pair[0]], points[pair[1]], color, 2)
            for point in points:
                if point:
                    cv2.circle(overlay, point, 3, color, -1)
            cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)
        else:
            # Обычная отрисовка
            for pair in skeleton_pairs:
                if points[pair[0]] and points[pair[1]]:
                    cv2.line(image, points[pair[0]], points[pair[1]], color, 2)
            for point in points:
                if point:
                    cv2.circle(image, point, 4, color, -1)
    
    def _compare_with_reference(self, user_points: List[Optional[Tuple[int, int]]]) -> dict:
        """Сравнивает позу пользователя с текущей эталонной позой"""
        if not self.reference_poses:
            return {"similarity": 0, "feedback": "No reference", "status": "error"}
        
        # Берем текущий эталонный кадр
        ref_idx = self.current_ref_frame % len(self.reference_poses)
        ref_points = self.reference_poses[ref_idx]
        
        # Нормализуем позы (убираем разницу в росте и позиции)
        user_norm = self._normalize_pose(user_points)
        ref_norm = self._normalize_pose(ref_points)
        
        # Считаем схожесть по позициям
        position_sim = self._calculate_position_similarity(user_norm, ref_norm)
        
        # Считаем схожесть по углам
        angle_sim = self._calculate_angle_similarity(user_points, ref_points)
        
        # Итоговая схожесть
        overall = position_sim * 0.5 + angle_sim * 0.5
        
        # Сохраняем в историю для сглаживания
        self.similarity_history.append(overall)
        smooth_similarity = np.mean(self.similarity_history) * 100
        
        # Генерируем обратную связь
        if overall > 0.8:
            feedback = "Отлично! Вы точно повторяете движение!"
            status = "excellent"
        elif overall > 0.6:
            feedback = "Хорошо! Продолжайте в том же духе!"
            status = "good"
        elif overall > 0.4:
            # Находим самую отличающуюся часть тела
            diff = np.linalg.norm(user_norm - ref_norm, axis=1)
            most_diff_idx = np.argmax(diff)
            
            body_parts = {
                0: "голову", 1: "шею", 2: "правое плечо", 3: "правый локоть",
                4: "правую кисть", 5: "левое плечо", 6: "левый локоть",
                7: "левую кисть", 8: "правое бедро", 9: "правое колено",
                10: "правую стопу", 11: "левое бедро", 12: "левое колено",
                13: "левую стопу"
            }
            part = body_parts.get(most_diff_idx, "позицию")
            feedback = f"Обратите внимание на {part}"
            status = "needs_improvement"
        else:
            feedback = "Постарайтесь точнее повторить движение"
            status = "poor"
        
        return {
            "similarity": round(smooth_similarity, 1),
            "position_match": round(position_sim * 100, 1),
            "angle_match": round(angle_sim * 100, 1),
            "feedback": feedback,
            "status": status
        }
    
    def _normalize_pose(self, points: List[Optional[Tuple[int, int]]]) -> np.ndarray:
        """Нормализует позу: центрирует и масштабирует"""
        valid = [p for p in points if p is not None]
        if len(valid) < 5:
            return np.zeros((18, 2))
        
        # Центр по шее (точка 1) или среднему
        neck = np.array(points[1]) if points[1] else np.mean(valid, axis=0)
        
        # Масштаб по расстоянию между плечами
        if points[2] and points[5]:
            scale = np.linalg.norm(np.array(points[2]) - np.array(points[5]))
        else:
            scale = 100
        
        if scale == 0:
            scale = 1
        
        normalized = np.zeros((18, 2))
        for i, p in enumerate(points):
            if p:
                normalized[i] = (np.array(p) - neck) / scale
        
        return normalized
    
    def _calculate_position_similarity(self, user_norm: np.ndarray, ref_norm: np.ndarray) -> float:
        """Схожесть по позициям точек"""
        mask = (user_norm.any(axis=1)) & (ref_norm.any(axis=1))
        if not mask.any():
            return 0.0
        
        distances = np.linalg.norm(user_norm[mask] - ref_norm[mask], axis=1)
        return max(0, 1 - np.mean(distances))
    
    def _calculate_angle_similarity(self, user_points: List, ref_points: List) -> float:
        """Схожесть по углам суставов"""
        # Определяем углы для сравнения
        angle_triplets = [
            (2, 3, 4),   # Правый локоть
            (5, 6, 7),   # Левый локоть
            (8, 9, 10),  # Правое колено
            (11, 12, 13), # Левое колено
            (1, 2, 3),   # Правое плечо
            (1, 5, 6),   # Левое плечо
        ]
        
        similarities = []
        for p1, p2, p3 in angle_triplets:
            if all([user_points[p1], user_points[p2], user_points[p3],
                    ref_points[p1], ref_points[p2], ref_points[p3]]):
                
                user_angle = self._calculate_angle(
                    user_points[p1], user_points[p2], user_points[p3]
                )
                ref_angle = self._calculate_angle(
                    ref_points[p1], ref_points[p2], ref_points[p3]
                )
                
                # Разница в углах (0° = идеально, 180° = худший случай)
                diff = min(abs(user_angle - ref_angle), 180)
                similarity = 1 - (diff / 90.0)  # 90° разницы = 0 схожести
                similarities.append(max(0, similarity))
        
        return np.mean(similarities) if similarities else 0.0
    
    def _calculate_angle(self, p1: Tuple, p2: Tuple, p3: Tuple) -> float:
        """Вычисляет угол между тремя точками"""
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        return np.degrees(np.arccos(cos_angle))
    
    def _error_response(self, msg: str) -> dict:
        return {
            "status": "error",
            "score": 0,
            "feedback": msg,
            "joints_detected": 0,
            "errors": [msg],
            "skeleton_image": None
        }