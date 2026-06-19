import base64
import json
import cv2
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.pose_analyzer import PoseAnalyzer, Joint

router = APIRouter()

_analyzer: PoseAnalyzer | None = None

def get_analyzer() -> PoseAnalyzer | None:
    global _analyzer
    if _analyzer is None:
        try:
            _analyzer = PoseAnalyzer()
        except Exception as e:
            print(f"PoseAnalyzer init failed: {e}")
    return _analyzer


def decode_frame(base64_str: str) -> np.ndarray | None:
    try:
        img_bytes = base64.b64decode(base64_str)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


def analyze_frame(frame: np.ndarray) -> dict:
    analyzer = get_analyzer()
    if analyzer is None:
        return {"score": 0, "joints": [], "errors": [{"joint": "Система", "message": "Анализатор позы недоступен"}]}

    try:
        joints, _ = analyzer.analyze_image(frame)
    except Exception as e:
        return {"score": 0, "joints": [], "errors": [{"joint": "Ошибка", "message": str(e)}]}

    visible = [j for j in joints if j is not None]
    errors = []

    def get(idx):
        return joints[idx] if idx < len(joints) else None

    # Минимум видимых точек для валидного анализа
    MIN_JOINTS = 8
    if len(visible) < MIN_JOINTS:
        errors.append({"joint": "Поза", "message": f"Встаньте в кадр полностью ({len(visible)}/{MIN_JOINTS} точек)"})
        joints_data = [{"id": i, "name": j.name, "x": j.x, "y": j.y, "confidence": round(j.confidence, 3)} for i, j in enumerate(joints) if j]
        return {"score": 0, "joints": joints_data, "errors": errors}

    nose = get(0)
    neck = get(1)
    r_shoulder = get(2)
    l_shoulder = get(5)
    r_hip = get(9)
    l_hip = get(12)
    r_knee = get(10)
    l_knee = get(13)
    r_elbow = get(3)
    l_elbow = get(6)

    img_h = frame.shape[0]
    img_w = frame.shape[1]

    # Плечи на одном уровне
    if r_shoulder and l_shoulder:
        dy = abs(r_shoulder.y - l_shoulder.y) / img_h
        if dy > 0.06:
            errors.append({"joint": "Плечи", "message": f"Выровняйте плечи (разница {dy*100:.0f}%)"})

    # Голова не опущена
    if nose and neck:
        if nose.y > neck.y:
            errors.append({"joint": "Голова", "message": "Поднимите голову"})

    # Симметрия бёдер
    if r_hip and l_hip:
        dy = abs(r_hip.y - l_hip.y) / img_h
        if dy > 0.07:
            errors.append({"joint": "Бёдра", "message": "Выровняйте корпус"})

    # Шея видна (базовая стойка)
    if not neck:
        errors.append({"joint": "Корпус", "message": "Отойдите дальше — корпус должен быть виден"})

    visibility_ratio = len(visible) / len(joints)
    base_score = int(visibility_ratio * 100)

    # Штраф за каждую ошибку
    penalty_per_error = 25
    score = max(0, base_score - len(errors) * penalty_per_error)

    joints_data = [{"id": i, "name": j.name, "x": j.x, "y": j.y, "confidence": round(j.confidence, 3)} for i, j in enumerate(joints) if j]
    return {"score": score, "joints": joints_data, "errors": errors}


@router.websocket("/ws/analyze/{exercise_name}")
async def analyze_exercise(websocket: WebSocket, exercise_name: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            base64_frame = payload.get("frame", "")

            frame = decode_frame(base64_frame)
            if frame is None:
                await websocket.send_text(json.dumps({"score": 0, "joints": [], "errors": [{"joint": "Кадр", "message": "Не удалось обработать изображение"}]}))
                continue

            result = analyze_frame(frame)
            await websocket.send_text(json.dumps(result))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except Exception:
            pass
