"""
Сервис анализа видео: извлекает углы суставов через OpenPose,
кэширует эталонные данные, сравнивает с видео пользователя.

Метод сравнения: амплитуда движения (range of motion).
Мы смотрим насколько каждый сустав сгибается/разгибается за упражнение,
а не абсолютные углы. Это устойчиво к разным углам камеры.
"""

import cv2
import json
import os
from typing import List, Optional, Dict, Tuple

from app.services.pose_analyzer import PoseAnalyzer, Joint

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'reference_cache')
REFERENCE_VIDEO_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'reference_videos')

# Тройки суставов (COCO 18 индексы): точка_до → вершина_угла → точка_после
ANGLE_JOINTS = {
    'left_elbow':  (5, 6, 7),    # ПлечоЛ → ЛоктьЛ → ЗапястьеЛ
    'right_elbow': (2, 3, 4),    # ПлечоП → ЛоктьП → ЗапястьеП
    'left_knee':   (11, 12, 13), # БедроЛ → КоленоЛ → ГоленьЛ
    'right_knee':  (8, 9, 10),   # БедроП → КоленоП → ГоленьП
    'left_hip':    (5, 11, 12),  # ПлечоЛ → БедроЛ → КоленоЛ
    'right_hip':   (2, 8, 9),    # ПлечоП → БедроП → КоленоП
    'spine':       (0, 1, 8),    # Нос → Шея → ПравоеБедро (approx)
}

ERROR_LABELS = {
    'left_elbow':  'Левый локоть',
    'right_elbow': 'Правый локоть',
    'left_knee':   'Левое колено',
    'right_knee':  'Правое колено',
    'left_hip':    'Левое бедро',
    'right_hip':   'Правое бедро',
    'spine':       'Осанка / спина',
}

# Подсказки когда пользователь двигается с недостаточной амплитудой
JOINT_ROM_HINTS = {
    'left_elbow':  'Сгибайте левую руку сильнее — амплитуда движения слишком мала',
    'right_elbow': 'Сгибайте правую руку сильнее — амплитуда движения слишком мала',
    'left_knee':   'Сгибайте левое колено глубже',
    'right_knee':  'Сгибайте правое колено глубже',
    'left_hip':    'Поднимайте левую ногу выше',
    'right_hip':   'Поднимайте правую ногу выше',
    'spine':       'Увеличьте наклон корпуса — спина двигается недостаточно',
}

# Минимальная амплитуда в эталоне (°), при которой сустав считается активным
MIN_REF_RANGE = 8.0
# Порог отношения амплитуды пользователя к эталону (0..1): ниже — показываем замечание
ROM_THRESHOLD = 0.55
# Максимальное число кадров для анализа
MAX_FRAMES = 50


class VideoAnalyzer:
    def __init__(self, pose_analyzer: PoseAnalyzer):
        self.analyzer = pose_analyzer
        os.makedirs(CACHE_DIR, exist_ok=True)

    def extract_angles_from_video(self, video_path: str) -> List[Dict[str, float]]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Не удалось открыть видео: {video_path}")

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        step = max(1, total // MAX_FRAMES)

        frames_data: List[Dict[str, float]] = []
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % step == 0:
                joints, _ = self.analyzer.analyze_image(frame)
                angles = self._joints_to_angles(joints)
                if len(angles) >= 3:
                    frames_data.append(angles)
            idx += 1

        cap.release()
        return frames_data

    def _joints_to_angles(self, joints: List[Optional[Joint]]) -> Dict[str, float]:
        angles: Dict[str, float] = {}
        for name, (a, b, c) in ANGLE_JOINTS.items():
            if a < len(joints) and b < len(joints) and c < len(joints):
                ja, jb, jc = joints[a], joints[b], joints[c]
                if ja and jb and jc:
                    angles[name] = round(self.analyzer.calculate_angle(ja, jb, jc), 1)
        return angles

    def get_reference_angles(self, exercise_id: str, reference_video_path: str) -> Optional[List[Dict[str, float]]]:
        cache_file = os.path.join(CACHE_DIR, f"{exercise_id}.json")

        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                data = json.load(f)
            if data:
                return data

        if not os.path.exists(reference_video_path):
            return None

        frames = self.extract_angles_from_video(reference_video_path)
        if frames:
            with open(cache_file, 'w') as f:
                json.dump(frames, f)
        return frames or None

    @staticmethod
    def _range_of_motion(frames: List[Dict[str, float]], joint: str) -> float:
        """Амплитуда движения сустава: max угол − min угол по всем кадрам."""
        values = [f[joint] for f in frames if joint in f]
        if len(values) < 2:
            return 0.0
        return max(values) - min(values)

    def compare(
        self,
        ref_frames: List[Dict[str, float]],
        user_frames: List[Dict[str, float]],
    ) -> Tuple[int, List[Dict[str, str]]]:
        """
        Сравнивает амплитуду движения суставов пользователя с эталоном.
        Не зависит от абсолютных углов (устойчиво к разным ракурсам камеры).
        """
        if not ref_frames or not user_frames:
            return 0, [{"joint": "Анализ", "message": "Недостаточно данных для сравнения"}]

        errors: List[Dict[str, str]] = []
        joint_scores: List[float] = []

        for joint in ANGLE_JOINTS.keys():
            ref_vals = [f[joint] for f in ref_frames if joint in f]
            user_vals = [f[joint] for f in user_frames if joint in f]

            if len(ref_vals) < 2 or len(user_vals) < 2:
                continue

            ref_rom = max(ref_vals) - min(ref_vals)

            # Пропускаем суставы, которые почти не двигаются в эталоне
            if ref_rom < MIN_REF_RANGE:
                continue

            user_rom = max(user_vals) - min(user_vals)

            # ROM score: насколько пользователь повторяет амплитуду движения
            rom_ratio = min(1.0, user_rom / ref_rom)

            # Overlap score: движется ли пользователь в той же угловой зоне?
            # Если поза другая — диапазоны углов не перекрываются → 0
            ref_min, ref_max = min(ref_vals), max(ref_vals)
            user_min, user_max = min(user_vals), max(user_vals)
            overlap = max(0.0, min(ref_max, user_max) - max(ref_min, user_min))
            overlap_ratio = overlap / ref_rom  # доля эталонного диапазона, покрытая пользователем

            # Итоговый коэффициент: 40% амплитуда + 60% угловая зона
            ratio = 0.4 * rom_ratio + 0.6 * overlap_ratio

            if ratio < ROM_THRESHOLD:
                label = ERROR_LABELS.get(joint, joint)
                hint = JOINT_ROM_HINTS.get(joint, 'Недостаточная амплитуда движения')
                errors.append({"joint": label, "message": hint})
                joint_scores.append(0.0)
            else:
                joint_scores.append(ratio * 100.0)

        if not joint_scores:
            # OpenPose не смог отследить движение ни одного сустава
            return 0, [{"joint": "Видео", "message": "Не удалось отследить движения. Встаньте дальше от камеры, чтобы всё тело было в кадре."}]

        score = int(sum(joint_scores) / len(joint_scores))
        return score, errors


def get_reference_video_path(exercise_id: str, video_url: Optional[str] = None) -> Optional[str]:
    path_by_id = os.path.join(REFERENCE_VIDEO_DIR, f"{exercise_id}.mp4")
    if os.path.exists(path_by_id):
        return path_by_id

    if video_url:
        filename = os.path.basename(video_url)
        if filename:
            path_by_url = os.path.join(REFERENCE_VIDEO_DIR, filename)
            if os.path.exists(path_by_url):
                return path_by_url

    try:
        videos = sorted(f for f in os.listdir(REFERENCE_VIDEO_DIR) if f.endswith('.mp4'))
        if videos:
            return os.path.join(REFERENCE_VIDEO_DIR, videos[0])
    except FileNotFoundError:
        pass

    return None


class MockVideoAnalyzer:
    """
    Fallback анализатор на основе детекции движения (не требует OpenPose).
    Сравнивает интенсивность движения по регионам кадра между видео пользователя и эталоном.
    """

    def __init__(self):
        self._cache: Dict[str, List[Dict[str, float]]] = {}

    def _extract_motion(self, video_path: str) -> List[Dict[str, float]]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        step = max(1, total // MAX_FRAMES)

        frames_data: List[Dict[str, float]] = []
        prev_gray = None
        idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % step == 0:
                h, w = frame.shape[:2]
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if prev_gray is not None:
                    diff = cv2.absdiff(gray, prev_gray).astype('float32')
                    regions: Dict[str, float] = {
                        'right_elbow': float(diff[:h // 2, :w // 2].mean()),
                        'left_elbow':  float(diff[:h // 2, w // 2:].mean()),
                        'right_knee':  float(diff[h // 2:, :w // 2].mean()),
                        'left_knee':   float(diff[h // 2:, w // 2:].mean()),
                        'right_hip':   float(diff[h // 3:2 * h // 3, :w // 2].mean()),
                        'left_hip':    float(diff[h // 3:2 * h // 3, w // 2:].mean()),
                        'spine':       float(diff[h // 4:3 * h // 4, w // 3:2 * w // 3].mean()),
                    }
                    frames_data.append(regions)
                prev_gray = gray
            idx += 1

        cap.release()
        return frames_data

    def extract_angles_from_video(self, video_path: str) -> List[Dict[str, float]]:
        return self._extract_motion(video_path)

    def get_reference_angles(self, exercise_id: str, ref_path: str) -> Optional[List[Dict[str, float]]]:
        if exercise_id in self._cache:
            return self._cache[exercise_id]
        if not os.path.exists(ref_path):
            return None
        frames = self._extract_motion(ref_path)
        if frames:
            self._cache[exercise_id] = frames
        return frames or None

    def compare(
        self,
        ref_frames: List[Dict[str, float]],
        user_frames: List[Dict[str, float]],
    ) -> Tuple[int, List[Dict[str, str]]]:
        if not ref_frames or not user_frames:
            return 0, [{"joint": "Анализ", "message": "Недостаточно данных для сравнения"}]

        errors: List[Dict[str, str]] = []
        joint_scores: List[float] = []

        for joint in ANGLE_JOINTS.keys():
            ref_avg = sum(f.get(joint, 0.0) for f in ref_frames) / len(ref_frames)
            if ref_avg < 2.0:
                continue

            user_avg = sum(f.get(joint, 0.0) for f in user_frames) / len(user_frames)
            ratio = min(1.0, user_avg / (ref_avg + 1e-6))
            joint_scores.append(ratio * 100.0)

            if ratio < ROM_THRESHOLD:
                label = ERROR_LABELS.get(joint, joint)
                hint = JOINT_ROM_HINTS.get(joint, 'Недостаточная амплитуда движения')
                errors.append({"joint": label, "message": hint})

        if not joint_scores:
            return 50, []

        return int(sum(joint_scores) / len(joint_scores)), errors
