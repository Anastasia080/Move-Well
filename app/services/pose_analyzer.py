"""
Pose Analyzer - основной класс для анализа позы
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple
from dataclasses import dataclass
import os

from app.services.openpose_processor import OpenPoseProcessor, Joint


class PoseAnalyzer:
    """Анализатор позы с использованием OpenPose"""
    
    def __init__(self, openpose_path: str = None, confidence_threshold: float = 0.3):
        """
        Инициализация анализатора
        
        Args:
            openpose_path: Путь к папке с OpenPose
            confidence_threshold: Порог уверенности для ключевых точек
        """
        if openpose_path is None:
            openpose_path = r"D:\openpose\openpose"
        
        self.openpose_path = openpose_path
        self.confidence_threshold = confidence_threshold
        self.processor = None
        
        print(f"PoseAnalyzer initialized with OpenPose at: {openpose_path}")
    
    def start(self):
        """Запуск процессора OpenPose"""
        if self.processor is None:
            self.processor = OpenPoseProcessor(self.openpose_path, self.confidence_threshold)
            self.processor.start()
            print("PoseAnalyzer processor started")
    
    def stop(self):
        """Остановка процессора"""
        if self.processor:
            self.processor.stop()
            self.processor = None
    
    def analyze_image(self, image: np.ndarray) -> Tuple[List[Optional[Joint]], np.ndarray]:
        """
        Анализ одного изображения
        
        Args:
            image: Изображение в формате numpy array (BGR)
            
        Returns:
            (список_суставов, изображение_с_скелетом)
        """
        # Если процессор не запущен, запускаем
        if self.processor is None:
            self.start()
        
        # Отправляем кадр на обработку
        self.processor.send_frame(image)
        
        # Получаем результат
        joints = self.processor.get_result()
        
        if joints is None:
            joints = [None] * 18
        
        # Рисуем скелет
        skeleton_image = self.draw_skeleton(image, joints)
        
        return joints, skeleton_image
    
    def draw_skeleton(self, image: np.ndarray, joints: List[Optional[Joint]]) -> np.ndarray:
        """Рисование скелета на изображении"""
        img = image.copy()
        h, w = img.shape[:2]
        
        # Соединения для скелета
        connections = [
            (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),
            (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13)
        ]
        
        # Рисуем соединения
        for start, end in connections:
            if start < len(joints) and end < len(joints):
                j1, j2 = joints[start], joints[end]
                if j1 and j2:
                    x1, y1 = int(j1.x), int(j1.y)
                    x2, y2 = int(j2.x), int(j2.y)
                    if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Рисуем ключевые точки
        for joint in joints:
            if joint:
                x, y = int(joint.x), int(joint.y)
                if 0 <= x < w and 0 <= y < h:
                    cv2.circle(img, (x, y), 4, (0, 0, 255), -1)
        
        return img
    
    def calculate_angle(self, a: Joint, b: Joint, c: Joint) -> float:
        """Вычисление угла между тремя суставами"""
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        
        ba = a - b
        bc = c - b
        
        cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        return np.degrees(np.arccos(np.clip(cos, -1, 1)))