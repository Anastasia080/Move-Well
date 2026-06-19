from fastapi import WebSocket, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.openpose_analyzer import OpenPoseAnalyzer
import json
import os
import base64
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import tempfile
import subprocess

analyzer = OpenPoseAnalyzer()

# Словарь эталонных видео (уже на сервере)
REFERENCE_VIDEOS = {
    "squat": "reference_videos/squat_reference.mp4",
    "pushup": "reference_videos/pushup_reference.mp4",
    "lunge": "reference_videos/lunge_reference.mp4",
    "stretching": "reference_videos/stretching_reference.mp4",
    "plank": "reference_videos/plank_reference.mp4",
    "general": "reference_videos/general_warmup.mp4",
}


class VideoComparator:
    """Класс для сравнения двух видео"""
    
    def __init__(self):
        self.analyzer = OpenPoseAnalyzer()
    
    def extract_poses_from_video(self, video_path: str, sample_rate: int = 3) -> List[Dict]:
        """Извлекает позы из видео"""
        print(f"Extracting poses from: {video_path}")
        
        if not os.path.exists(video_path):
            raise Exception(f"Video file not found: {video_path}")
        
        # Проверяем размер файла
        file_size = os.path.getsize(video_path)
        print(f"File size: {file_size} bytes")
        if file_size < 1000:
            raise Exception("Video file is too small or empty")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Cannot open video: {video_path}. Format may not be supported.")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Total frames: {total_frames}, FPS: {fps}")
        
        # Если total_frames = 0, пробуем считать кадры вручную
        if total_frames <= 0:
            print("Warning: total_frames is 0, trying to count frames manually...")
            ret, test_frame = cap.read()
            if not ret or test_frame is None:
                cap.release()
                raise Exception("Cannot read frames from video. The video format may not be supported.")
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            total_frames = 0
            
            while True:
                ret, _ = cap.read()
                if not ret:
                    break
                total_frames += 1
            
            cap.release()
            cap = cv2.VideoCapture(video_path)
            print(f"Manually counted frames: {total_frames}")
        
        if total_frames <= 0:
            cap.release()
            raise Exception("Video has no readable frames")
        
        poses = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            
            if frame_idx % sample_rate == 0:
                try:
                    points = self._extract_points(frame)
                    
                    if points:
                        detected = sum(1 for p in points if p is not None)
                        if detected >= 5:
                            poses.append({
                                "frame_idx": frame_idx,
                                "timestamp": frame_idx / fps if fps and fps > 0 else frame_idx / 30.0,
                                "points": points,
                                "detected": detected
                            })
                except Exception as e:
                    print(f"  Warning: Error extracting points from frame {frame_idx}: {e}")
            
            frame_idx += 1
            
            if frame_idx % 50 == 0 and total_frames > 0:
                progress = (frame_idx / total_frames) * 100
                print(f"  Progress: {progress:.1f}% ({len(poses)} poses)")
        
        cap.release()
        
        if len(poses) == 0:
            raise Exception("No poses could be extracted. Make sure a person is visible in the video.")
        
        print(f"Extracted {len(poses)} poses from {frame_idx} frames")
        return poses
    
    def _extract_points(self, frame: np.ndarray) -> List[Optional[Tuple[int, int]]]:
        """Извлекает ключевые точки из кадра"""
        h, w = frame.shape[:2]
        
        blob = cv2.dnn.blobFromImage(
            frame, 1.0/255.0, (368, 368), (0, 0, 0), swapRB=False, crop=False
        )
        
        self.analyzer.net.setInput(blob)
        output = self.analyzer.net.forward()
        
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
    
    def compare_videos(self, reference_poses: List[Dict], user_poses: List[Dict]) -> Dict:
        """Сравнивает две последовательности поз"""
        print(f"\nComparing videos:")
        print(f"  Reference poses: {len(reference_poses)}")
        print(f"  User poses: {len(user_poses)}")
        
        if not reference_poses or not user_poses:
            return {
                "status": "error",
                "message": "Не удалось извлечь позы из видео. Убедитесь, что человек виден в кадре.",
                "overall_similarity": 0,
                "frame_comparisons": []
            }
        
        comparisons = []
        similarities = []
        
        ref_duration = reference_poses[-1]["timestamp"] if reference_poses else 1
        user_duration = user_poses[-1]["timestamp"] if user_poses else 1
        
        print(f"Ref duration: {ref_duration:.1f}s, User duration: {user_duration:.1f}s")
        
        for user_pose in user_poses:
            if user_duration > 0:
                user_time_norm = user_pose["timestamp"] / user_duration
            else:
                user_time_norm = 0
            
            target_time = user_time_norm * ref_duration
            ref_pose = min(reference_poses, 
                          key=lambda x: abs(x["timestamp"] - target_time))
            
            similarity_score = self._compare_poses(ref_pose["points"], user_pose["points"])
            
            comparisons.append({
                "user_frame": user_pose["frame_idx"],
                "ref_frame": ref_pose["frame_idx"],
                "similarity": similarity_score,
                "user_time": user_pose["timestamp"],
                "ref_time": ref_pose["timestamp"]
            })
            similarities.append(similarity_score)
        
        overall_similarity = np.mean(similarities) if similarities else 0
        
        if comparisons:
            best_match = max(comparisons, key=lambda x: x["similarity"])
            worst_match = min(comparisons, key=lambda x: x["similarity"])
        else:
            best_match = None
            worst_match = None
        
        # Строгие пороги оценок
        if overall_similarity >= 85:
            rating = "Отлично"
            feedback = "Превосходно! Техника выполнения практически идентична эталону."
        elif overall_similarity >= 70:
            rating = "Хорошо"
            feedback = "Хорошая техника! Есть небольшие отклонения, но в целом правильно."
        elif overall_similarity >= 55:
            rating = "Удовлетворительно"
            feedback = "Неплохо, но есть заметные отличия от эталона. Обратите внимание на углы в суставах."
        elif overall_similarity >= 40:
            rating = "Ниже среднего"
            feedback = "Техника требует улучшения. Старайтесь точнее повторять движения."
        elif overall_similarity >= 25:
            rating = "Плохо"
            feedback = "Значительные отличия от эталона. Рекомендуется внимательно изучить правильную технику."
        else:
            rating = "Очень плохо"
            feedback = "Движения сильно отличаются от эталона. Возможно, выполняется другое упражнение."
        
        result = {
            "status": "success",
            "overall_similarity": round(overall_similarity, 1),
            "rating": rating,
            "feedback": feedback,
            "best_match": {
                "similarity": round(best_match["similarity"], 1),
                "user_frame": best_match["user_frame"],
                "ref_frame": best_match["ref_frame"]
            } if best_match else None,
            "worst_match": {
                "similarity": round(worst_match["similarity"], 1),
                "user_frame": worst_match["user_frame"],
                "ref_frame": worst_match["ref_frame"]
            } if worst_match else None,
            "total_comparisons": len(comparisons),
            "avg_similarity_per_frame": round(overall_similarity, 1)
        }
        
        print(f"\nComparison results:")
        print(f"  Overall similarity: {overall_similarity:.1f}%")
        print(f"  Rating: {rating}")
        
        return result
    
    def _compare_poses(self, ref_points: List, user_points: List) -> float:
        """Сравнивает две позы. Возвращает схожесть в процентах (0-100)"""
        ref_valid = sum(1 for p in ref_points if p is not None)
        user_valid = sum(1 for p in user_points if p is not None)
        
        if ref_valid < 5 or user_valid < 5:
            return 0.0
        
        position_similarity = self._compare_positions_strict(ref_points, user_points)
        angle_similarity = self._compare_angles_strict(ref_points, user_points)
        distance_similarity = self._compare_distances(ref_points, user_points)
        
        overall = (position_similarity * 0.4 + angle_similarity * 0.4 + distance_similarity * 0.2) * 100
        
        return overall
    
    def _compare_positions_strict(self, ref_points: List, user_points: List) -> float:
        """Строгое сравнение позиций точек"""
        ref_norm = self._normalize_pose(ref_points)
        user_norm = self._normalize_pose(user_points)
        
        critical_points = [1, 2, 5, 8, 11]
        
        critical_ref = all(ref_points[i] is not None for i in critical_points)
        critical_user = all(user_points[i] is not None for i in critical_points)
        
        if not critical_ref or not critical_user:
            return 0.0
        
        common_points = []
        for i in range(18):
            if ref_points[i] is not None and user_points[i] is not None:
                dist = np.linalg.norm(ref_norm[i] - user_norm[i])
                common_points.append(dist)
        
        if not common_points:
            return 0.0
        
        avg_distance = np.mean(common_points)
        
        if avg_distance < 0.1:
            similarity = 1.0
        elif avg_distance < 0.5:
            similarity = 1.0 - (avg_distance - 0.1) * 1.25
        elif avg_distance < 1.0:
            similarity = 0.5 - (avg_distance - 0.5) * 0.8
        elif avg_distance < 1.5:
            similarity = 0.1 - (avg_distance - 1.0) * 0.2
        else:
            similarity = 0.0
        
        missing_penalty = 0.0
        for i in critical_points:
            if ref_points[i] is None or user_points[i] is None:
                missing_penalty += 0.15
        
        similarity = max(0, similarity - missing_penalty)
        
        return similarity
    
    def _compare_angles_strict(self, ref_points: List, user_points: List) -> float:
        """Строгое сравнение углов суставов"""
        angle_triplets = {
            'right_elbow': (2, 3, 4),
            'left_elbow': (5, 6, 7),
            'right_knee': (8, 9, 10),
            'left_knee': (11, 12, 13),
            'right_shoulder': (1, 2, 3),
            'left_shoulder': (1, 5, 6),
            'right_hip': (1, 8, 9),
            'left_hip': (1, 11, 12),
        }
        
        angle_similarities = []
        weights = []
        
        for joint_name, (p1_idx, p2_idx, p3_idx) in angle_triplets.items():
            if all([
                ref_points[p1_idx] is not None,
                ref_points[p2_idx] is not None,
                ref_points[p3_idx] is not None,
                user_points[p1_idx] is not None,
                user_points[p2_idx] is not None,
                user_points[p3_idx] is not None
            ]):
                ref_angle = self._calculate_angle(
                    ref_points[p1_idx], ref_points[p2_idx], ref_points[p3_idx]
                )
                user_angle = self._calculate_angle(
                    user_points[p1_idx], user_points[p2_idx], user_points[p3_idx]
                )
                
                angle_diff = abs(ref_angle - user_angle)
                
                if angle_diff <= 5:
                    similarity = 1.0
                elif angle_diff <= 15:
                    similarity = 0.8 - (angle_diff - 5) * 0.02
                elif angle_diff <= 30:
                    similarity = 0.6 - (angle_diff - 15) * 0.02
                elif angle_diff <= 45:
                    similarity = 0.3 - (angle_diff - 30) * 0.013
                else:
                    similarity = 0.0
                
                angle_similarities.append(similarity)
                
                if 'knee' in joint_name or 'elbow' in joint_name:
                    weights.append(1.5)
                else:
                    weights.append(1.0)
        
        if not angle_similarities:
            return 0.0
        
        weighted_sum = sum(s * w for s, w in zip(angle_similarities, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _compare_distances(self, ref_points: List, user_points: List) -> float:
        """Сравнивает относительные расстояния между ключевыми точками"""
        distance_pairs = [
            (2, 5), (8, 11), (1, 8), (8, 9), (9, 10),
        ]
        
        distance_ratios = []
        
        for p1_idx, p2_idx in distance_pairs:
            if all([
                ref_points[p1_idx] is not None,
                ref_points[p2_idx] is not None,
                user_points[p1_idx] is not None,
                user_points[p2_idx] is not None
            ]):
                ref_dist = np.linalg.norm(
                    np.array(ref_points[p1_idx]) - np.array(ref_points[p2_idx])
                )
                user_dist = np.linalg.norm(
                    np.array(user_points[p1_idx]) - np.array(user_points[p2_idx])
                )
                
                if ref_dist > 0:
                    ratio = min(ref_dist, user_dist) / max(ref_dist, user_dist)
                    
                    if ratio > 0.95:
                        similarity = 1.0
                    elif ratio > 0.85:
                        similarity = 0.8
                    elif ratio > 0.75:
                        similarity = 0.6
                    elif ratio > 0.65:
                        similarity = 0.4
                    elif ratio > 0.5:
                        similarity = 0.2
                    else:
                        similarity = 0.0
                    
                    distance_ratios.append(similarity)
        
        return np.mean(distance_ratios) if distance_ratios else 0.0
    
    def _normalize_pose(self, points: List) -> np.ndarray:
        """Нормализует позу: центрирует относительно шеи и масштабирует"""
        valid = [p for p in points if p is not None]
        if len(valid) < 5:
            return np.zeros((18, 2))
        
        if points[1] is not None:
            neck = np.array(points[1])
        else:
            neck = np.mean(valid, axis=0)
        
        if points[2] is not None and points[5] is not None:
            scale = np.linalg.norm(np.array(points[2]) - np.array(points[5]))
        else:
            scale = 100
        
        if scale < 1:
            scale = 1
        
        normalized = np.zeros((18, 2))
        for i, p in enumerate(points):
            if p is not None:
                normalized[i] = (np.array(p) - neck) / scale
        
        return normalized
    
    def _calculate_angle(self, p1: Tuple, p2: Tuple, p3: Tuple) -> float:
        """Вычисляет угол между тремя точками в градусах (0-180)"""
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 < 1 or norm_v2 < 1:
            return 0
        
        cos_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        return np.degrees(np.arccos(cos_angle))
    
    def convert_video_to_mp4(self, input_path: str) -> str:
        """Конвертирует видео в MP4 формат для лучшей совместимости"""
        output_path = input_path.rsplit('.', 1)[0] + '_converted.mp4'
        
        # Способ 1: Пробуем через FFmpeg
        try:
            result = subprocess.run([
                'ffmpeg', '-y', '-i', input_path,
                '-c:v', 'libx264', '-preset', 'fast',
                '-crf', '23', '-an',
                output_path
            ], capture_output=True, text=True, timeout=60)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                print(f"Converted with FFmpeg: {output_path}")
                return output_path
        except FileNotFoundError:
            print("FFmpeg not found, trying OpenCV conversion...")
        except Exception as e:
            print(f"FFmpeg error: {e}")
        
        # Способ 2: Конвертация через OpenCV
        try:
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise Exception("Cannot open video for conversion")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if width <= 0 or height <= 0:
                cap.release()
                raise Exception("Invalid video dimensions")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                frame_count += 1
            
            cap.release()
            out.release()
            
            if frame_count > 0 and os.path.getsize(output_path) > 1000:
                print(f"Converted with OpenCV: {frame_count} frames to {output_path}")
                return output_path
            else:
                print("OpenCV conversion produced empty file")
                if os.path.exists(output_path):
                    os.unlink(output_path)
                return input_path
                
        except Exception as e:
            print(f"OpenCV conversion error: {e}")
            if os.path.exists(output_path):
                os.unlink(output_path)
            return input_path


# Создаем экземпляр компаратора
video_comparator = VideoComparator()


# WebSocket handler для real-time анализа
async def handle_websocket(websocket: WebSocket, exercise: str):
    await websocket.accept()
    
    try:
        auth_data = await websocket.receive_json()
        token = auth_data.get("token")
        
        if not token:
            await websocket.send_json({"error": "No token provided"})
            await websocket.close()
            return
        
        print(f"User connected (demo mode)")
        
        await websocket.send_json({
            "status": "connected", 
            "message": "Connected to MoveWell",
            "exercise": exercise
        })
        
        frame_count = 0
        while True:
            data = await websocket.receive_json()
            image_base64 = data.get("image")
            
            if not image_base64:
                continue
            
            frame_count += 1
            result = analyzer.process_frame(image_base64, exercise)
            result["frame_number"] = frame_count
            
            await websocket.send_json(result)
            
    except Exception as e:
        print(f"Error in websocket handler: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except:
            pass
        try:
            await websocket.close()
        except:
            pass


# Endpoint для сравнения видео пользователя с эталоном на сервере
async def compare_videos_endpoint(
    user_video: UploadFile = File(...),
    exercise: str = Form("general")
):
    """Сравнивает видео пользователя с эталонным видео на сервере"""
    try:
        # Проверяем, есть ли эталон для этого упражнения
        if exercise not in REFERENCE_VIDEOS:
            return JSONResponse({
                "status": "error",
                "message": f"Нет эталонного видео для упражнения '{exercise}'. Доступные: {list(REFERENCE_VIDEOS.keys())}",
                "overall_similarity": 0
            }, status_code=400)
        
        ref_path = REFERENCE_VIDEOS[exercise]
        
        if not os.path.exists(ref_path):
            return JSONResponse({
                "status": "error",
                "message": f"Эталонное видео не найдено на сервере. Ожидаемый путь: {ref_path}",
                "overall_similarity": 0
            }, status_code=404)
        
        # Сохраняем видео пользователя во временный файл
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as user_tmp:
            user_content = await user_video.read()
            user_tmp.write(user_content)
            user_path = user_tmp.name
        
        print(f"\n{'='*60}")
        print(f"Video comparison: {exercise}")
        print(f"Reference (server): {ref_path}")
        print(f"User video: {user_video.filename} ({len(user_content)} bytes)")
        print(f"{'='*60}")
        
        # Конвертируем видео если нужно
        final_user_path = user_path
        if user_path.endswith('.webm'):
            print("\nConverting WebM to MP4 for better compatibility...")
            converted_path = video_comparator.convert_video_to_mp4(user_path)
            if converted_path != user_path:
                final_user_path = converted_path
                try:
                    os.unlink(user_path)
                except:
                    pass
        
        # Извлекаем позы из эталонного видео
        print("\n1. Extracting poses from reference video...")
        ref_poses = video_comparator.extract_poses_from_video(ref_path)
        
        # Извлекаем позы из видео пользователя
        print("\n2. Extracting poses from user video...")
        user_poses = video_comparator.extract_poses_from_video(final_user_path)
        
        # Сравниваем позы
        print("\n3. Comparing poses...")
        result = video_comparator.compare_videos(ref_poses, user_poses)
        
        # Добавляем информацию об упражнении
        result["exercise"] = exercise
        result["reference_video"] = ref_path
        
        # Очищаем временные файлы
        try:
            if os.path.exists(final_user_path):
                os.unlink(final_user_path)
        except:
            pass
        
        print(f"\nComparison complete! Similarity: {result.get('overall_similarity', 0)}%")
        
        return JSONResponse(result)
        
    except Exception as e:
        print(f"Error in compare_videos_endpoint: {e}")
        import traceback
        traceback.print_exc()
        
        # Очищаем временные файлы в случае ошибки
        try:
            if 'user_path' in locals() and os.path.exists(user_path):
                os.unlink(user_path)
            if 'final_user_path' in locals() and os.path.exists(final_user_path):
                os.unlink(final_user_path)
        except:
            pass
        
        return JSONResponse({
            "status": "error",
            "message": str(e),
            "overall_similarity": 0
        }, status_code=500)