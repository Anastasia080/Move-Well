"""
Модуль для анализа позы через OpenPose
"""

import subprocess
import json
import cv2
import numpy as np
import os
import tempfile
import shutil
from typing import List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Joint:
    """Ключевая точка скелета"""
    x: float
    y: float
    confidence: float
    name: str

class PoseAnalyzer:
    """Анализатор позы с использованием OpenPose"""
    
    # Индексы ключевых точек OpenPose (COCO/BODY_25)
    JOINT_NAMES = {
        0: "nose", 1: "neck", 2: "right_shoulder", 3: "right_elbow",
        4: "right_wrist", 5: "left_shoulder", 6: "left_elbow", 7: "left_wrist",
        8: "right_hip", 9: "right_knee", 10: "right_ankle", 11: "left_hip",
        12: "left_knee", 13: "left_ankle", 14: "right_eye", 15: "left_eye",
        16: "right_ear", 17: "left_ear", 18: "background"
    }
    
    # Важные соединения для рисования скелета
    SKELETON_CONNECTIONS = [
        (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),  # Руки
        (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),  # Ноги
        (1, 0), (0, 14), (14, 16), (0, 15), (15, 17)  # Голова
    ]
    
    def __init__(self, openpose_path: str = None, confidence_threshold: float = 0.3):
        """
        Инициализация анализатора
        
        Args:
            openpose_path: Путь к папке с OpenPose (где лежит bin/OpenPoseDemo.exe)
            confidence_threshold: Порог уверенности для ключевых точек
        """
        if openpose_path is None:
            possible_paths = [
                r"D:\openpose\openpose",
                r"C:\openpose",
                r"C:\Program Files\openpose",
                Path(__file__).parent.parent.parent / "openpose"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    openpose_path = str(path)
                    break
        
        self.openpose_path = openpose_path
        self.openpose_exe = os.path.join(openpose_path, "bin", "OpenPoseDemo.exe")
        self.confidence_threshold = confidence_threshold
        
        if not os.path.exists(self.openpose_exe):
            raise FileNotFoundError(f"OpenPose not found at {self.openpose_exe}")
        
        print(f"PoseAnalyzer initialized with OpenPose at: {openpose_path}")
    
    def analyze_image(self, image: np.ndarray) -> Tuple[List[Optional[Joint]], np.ndarray]:
        """
        Анализ одного изображения
        
        Args:
            image: Изображение в формате numpy array (BGR)
            
        Returns:
            (список_суставов, изображение_с_скелетом)
        """
        print(f"Analyzing image with shape: {image.shape}")
        
        # Создаем временную папку для изображения
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "frame.jpg")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        cv2.imwrite(input_path, image)
        print(f"📸 Saved temp image: {input_path}")
        
        try:
            # Запускаем OpenPose через image_dir (без флага --image)
            cmd = [
                self.openpose_exe,
                "--image_dir", temp_dir,
                "--write_json", output_dir,
                "--display", "0",
                "--render_pose", "0",
                "--model_pose", "BODY_25",
                "--num_gpu", "0"
            ]
            
            print(f"Running OpenPose...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"OpenPose return code: {result.returncode}")
                if result.stderr:
                    print(f"Stderr: {result.stderr[:500]}")
            
            # Парсим результат из output_dir
            joints = self._parse_openpose_output(output_dir)
            
            visible_count = sum(1 for j in joints if j is not None)
            print(f"Visible joints: {visible_count}/18")
            
            # Рисуем скелет на изображении
            skeleton_image = self.draw_skeleton(image, joints)
            
            return joints, skeleton_image
            
        except subprocess.TimeoutExpired:
            print("OpenPose timeout")
            return [None] * 18, image
        except Exception as e:
            print(f"OpenPose error: {e}")
            return [None] * 18, image
        finally:
            # Чистим временные файлы
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def analyze_video_frame(self, frame: np.ndarray) -> List[Optional[Joint]]:
        """Анализ одного кадра видео (упрощенная версия)"""
        return self.analyze_image(frame)[0]
    
    def _parse_openpose_output(self, output_dir: str) -> List[Optional[Joint]]:
        """Парсинг JSON выхода OpenPose"""
        joints = [None] * 19
        
        try:
            # Ищем JSON файл в output_dir
            json_files = []
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    if f.endswith('.json'):
                        json_files.append(os.path.join(root, f))
            
            if not json_files:
                print("No JSON files found in output directory")
                return joints
            
            with open(json_files[0], 'r') as f:
                data = json.load(f)
            
            if "people" in data and len(data["people"]) > 0:
                person = data["people"][0]
                print(f"Found {len(data['people'])} person(s) in frame")
                
                if "pose_keypoints_2d" in person:
                    keypoints = person["pose_keypoints_2d"]
                    num_points = len(keypoints) // 3
                    
                    for i in range(min(num_points, 19)):
                        x = keypoints[i*3]
                        y = keypoints[i*3+1]
                        confidence = keypoints[i*3+2]
                        
                        if confidence > self.confidence_threshold:
                            joints[i] = Joint(
                                x=x, y=y,
                                confidence=confidence,
                                name=self.JOINT_NAMES.get(i, f"joint_{i}")
                            )
            else:
                print("No people detected in frame")
                
        except Exception as e:
            print(f"Error parsing OpenPose output: {e}")
        
        return joints
    
    def draw_skeleton(self, image: np.ndarray, joints: List[Optional[Joint]]) -> np.ndarray:
        """Рисование скелета на изображении"""
        img = image.copy()
        h, w = img.shape[:2]
        
        # Рисуем ключевые точки
        for i, joint in enumerate(joints):
            if joint is not None:
                x = int(joint.x)
                y = int(joint.y)
                
                if 0 <= x < w and 0 <= y < h:
                    color = (0, int(255 * joint.confidence), 0)
                    cv2.circle(img, (x, y), 5, color, -1)
                    cv2.putText(img, str(i), (x + 5, y - 5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        # Рисуем соединения
        for start, end in self.SKELETON_CONNECTIONS:
            if start < len(joints) and end < len(joints):
                joint_start = joints[start]
                joint_end = joints[end]
                
                if joint_start and joint_end:
                    x1, y1 = int(joint_start.x), int(joint_start.y)
                    x2, y2 = int(joint_end.x), int(joint_end.y)
                    
                    if (0 <= x1 < w and 0 <= y1 < h and 
                        0 <= x2 < w and 0 <= y2 < h):
                        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        return img
    
    def calculate_angle(self, joint_a: Joint, joint_b: Joint, joint_c: Joint) -> float:
        """Вычисление угла между тремя суставами"""
        a = np.array([joint_a.x, joint_a.y])
        b = np.array([joint_b.x, joint_b.y])
        c = np.array([joint_c.x, joint_c.y])
        
        ba = a - b
        bc = c - b
        
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        
        return np.degrees(angle)