import mediapipe as mp
import numpy as np
from typing import List, Dict
from app.schemas.pose import PoseFrame, PoseComparisonResult
from app.utils.pose_comparison import compare_angles
from app.utils.error_detection import detect_errors

class PoseService:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def extract_landmarks(self, frame_bytes: bytes) -> List[Dict]:
        """
        Извлечение ключевых точек из кадра (если фронтенд шлёт сырые кадры)
        Но по нашей архитекме фронтенд уже делает MediaPipe локально
        """
        # Этот метод не нужен, если фронтенд уже присылает координаты
        pass
    
    def compare_with_etalon(
        self, 
        user_poses: List[PoseFrame], 
        exercise_id: int
    ) -> PoseComparisonResult:
        """
        Сравнение последовательности поз пользователя с эталоном
        """
        # 1. Загрузить эталонные точки из БД (exercises.key_points)
        # 2. Вычислить углы в суставах для каждого кадра
        # 3. Сравнить с эталонными углами (допуск ±15%)
        # 4. Определить ошибки
        # 5. Вернуть результат
        
        angles_user = self._calculate_angles(user_poses)
        angles_etalon = self._get_etalon_angles(exercise_id)
        
        similarity = self._compute_similarity(angles_user, angles_etalon)
        errors = detect_errors(angles_user, angles_etalon)
        
        if similarity > 0.85:
            result = "success"
        elif similarity > 0.60:
            result = "partial"
        else:
            result = "fail"
        
        return PoseComparisonResult(
            result=result,
            errors=errors,
            score=similarity * 100
        )
    
    def _calculate_angles(self, poses: List[PoseFrame]) -> np.ndarray:
        """Вычисление углов в ключевых суставах"""
        # Углы: плечо, локоть, бедро, колено, голеностоп
        pass
    
    def _get_etalon_angles(self, exercise_id: int) -> np.ndarray:
        """Загрузка эталонных углов из БД"""
        pass
    
    def _compute_similarity(self, user_angles, etalon_angles) -> float:
        """DTW (Dynamic Time Warping) для сравнения временных рядов"""
        from scipy.spatial.distance import euclidean
        from fastdtw import fastdtw
        
        distance, _ = fastdtw(user_angles, etalon_angles, dist=euclidean)
        similarity = 1 / (1 + distance)
        return similarity