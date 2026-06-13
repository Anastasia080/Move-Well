"""
Модуль валидации упражнений - сравнивает позу пользователя с эталоном
"""

from typing import List, Optional, Dict, Tuple
from app.services.pose_analyzer import PoseAnalyzer, Joint

class ExerciseValidator:
    """Валидатор выполнения упражнений"""
    
    # Эталонные углы для разных упражнений (в градусах)
    EXERCISE_ANGLES = {
        "squat": {
            "left_knee": {"min": 80, "max": 110, "joints": [11, 12, 13]},  # hip, knee, ankle
            "right_knee": {"min": 80, "max": 110, "joints": [8, 9, 10]},
            "back": {"min": 10, "max": 30, "joints": [1, 8, 9]}  # neck, hip, knee
        },
        "pushup": {
            "left_elbow": {"min": 60, "max": 100, "joints": [5, 6, 7]},
            "right_elbow": {"min": 60, "max": 100, "joints": [2, 3, 4]},
            "body_alignment": {"min": 170, "max": 190, "joints": [1, 8, 9]}
        },
        "plank": {
            "left_elbow": {"min": 80, "max": 100, "joints": [5, 6, 7]},
            "right_elbow": {"min": 80, "max": 100, "joints": [2, 3, 4]},
            "body_alignment": {"min": 170, "max": 190, "joints": [1, 8, 9]}
        }
    }
    
    def __init__(self, pose_analyzer: PoseAnalyzer):
        self.pose_analyzer = pose_analyzer
    
    def validate_exercise(self, 
                          user_joints: List[Optional[Joint]], 
                          exercise_name: str) -> Dict:
        """
        Проверка выполнения упражнения
        
        Args:
            user_joints: Суставы пользователя
            exercise_name: Название упражнения
            
        Returns:
            Результат валидации с ошибками и оценкой
        """
        if exercise_name not in self.EXERCISE_ANGLES:
            return {
                "score": 0,
                "status": "unknown",
                "errors": [f"Упражнение {exercise_name} не найдено"],
                "feedback": "Упражнение не распознано"
            }
        
        exercise_config = self.EXERCISE_ANGLES[exercise_name]
        errors = []
        
        for angle_name, config in exercise_config.items():
            joint_indices = config["joints"]
            
            # Проверяем, что все суставы есть
            joints_valid = all(
                idx < len(user_joints) and user_joints[idx] is not None
                for idx in joint_indices
            )
            
            if not joints_valid:
                errors.append({
                    "joint": angle_name,
                    "error": "не удается определить положение",
                    "severity": "high"
                })
                continue
            
            # Вычисляем угол
            a, b, c = joint_indices
            angle = self.pose_analyzer.calculate_angle(
                user_joints[a], user_joints[b], user_joints[c]
            )
            
            # Проверяем попадание в диапазон
            if angle < config["min"]:
                errors.append({
                    "joint": angle_name,
                    "error": f"угол слишком маленький ({angle:.0f}° вместо {config['min']}-{config['max']}°)",
                    "severity": "medium",
                    "actual": angle,
                    "expected_min": config["min"],
                    "expected_max": config["max"]
                })
            elif angle > config["max"]:
                errors.append({
                    "joint": angle_name,
                    "error": f"угол слишком большой ({angle:.0f}° вместо {config['min']}-{config['max']}°)",
                    "severity": "medium",
                    "actual": angle,
                    "expected_min": config["min"],
                    "expected_max": config["max"]
                })
        
        # Вычисляем оценку (0-100%)
        error_count = len(errors)
        max_errors = len(exercise_config)
        score = max(0, 100 - (error_count / max_errors) * 100)
        
        # Определяем статус
        if score >= 80:
            status = "good"
            feedback = "Отлично! Упражнение выполнено правильно"
        elif score >= 50:
            status = "needs_improvement"
            feedback = "Хорошо, но есть ошибки. Обратите внимание на технику"
        else:
            status = "poor"
            feedback = "Требуется повторить упражнение. Внимательно следите за положением тела"
        
        return {
            "score": round(score),
            "status": status,
            "errors": errors,
            "feedback": feedback,
            "angles_checked": len(exercise_config),
            "errors_count": error_count
        }