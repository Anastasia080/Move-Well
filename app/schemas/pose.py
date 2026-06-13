from pydantic import BaseModel
from typing import List, Tuple, Optional
from enum import Enum

class PoseLandmark(BaseModel):
    """Одна ключевая точка скелета"""
    x: float          # 0-1 (относительно ширины кадра)
    y: float          # 0-1 (относительно высоты кадра)
    z: float          # глубина
    visibility: float # 0-1 (насколько точка видна)

class PoseFrame(BaseModel):
    """Один кадр с координатами скелета"""
    landmarks: List[PoseLandmark]  # 33 точки (MediaPipe Pose)
    timestamp: float                # время от начала упражнения (сек)

class PoseComparisonResult(BaseModel):
    """Результат сравнения позы с эталоном"""
    result: str                     # "success", "fail", "partial"
    errors: List[str]               # ['knee_valgus', 'lumbar_arch']
    score: float                    # 0-100 (общая точность)
    details: Optional[dict] = None  # детали по суставам