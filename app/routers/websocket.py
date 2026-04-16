from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import cv2
import base64
import json
import numpy as np
from datetime import datetime
import uuid

from app.database import get_db
from app.models import User, SessionProgress, SessionFrameAnalysis
from app.auth_utils import get_current_user_ws
from app.services.pose_analyzer import PoseAnalyzer
from app.services.exercise_validator import ExerciseValidator

router = APIRouter(tags=["WebSocket"])

# Инициализация сервисов OpenPose
pose_analyzer = PoseAnalyzer(openpose_path=r"D:\openpose\openpose")
validator = ExerciseValidator(pose_analyzer)


@router.websocket("/ws/analyze/{exercise_name}")
async def websocket_analyze(
    websocket: WebSocket,
    exercise_name: str
):
    """WebSocket для анализа выполнения упражнений"""
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    user_id = None
    
    try:
        # Получаем токен авторизации
        init_data = await websocket.receive_text()
        init_json = json.loads(init_data)
        token = init_json.get("token")
        
        # Аутентификация (упрощенно, нужно реализовать)
        # user = await get_current_user_ws(token)
        
        print(f"Session started: {session_id}, exercise: {exercise_name}")
        
        # Основной цикл
        while True:
            # Получаем кадр
            data = await websocket.receive_text()
            frame_data = json.loads(data)
            
            if "image" not in frame_data:
                continue
            
            # Декодируем изображение
            image_bytes = base64.b64decode(frame_data["image"])
            np_arr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is None:
                continue
            
            # Анализируем позу через OpenPose
            joints, skeleton_image = pose_analyzer.analyze_image(frame)
            
            # Проверяем выполнение упражнения
            visible_joints = sum(1 for j in joints if j is not None)
            
            if visible_joints < 5:
                # Недостаточно точек для анализа
                result = {
                    "session_id": session_id,
                    "frame": 0,
                    "status": "no_person",
                    "feedback": "Пользователь не обнаружен. Встаньте в кадр.",
                    "score": 0,
                    "errors": [],
                    "joints_detected": visible_joints
                }
            else:
                # Валидируем упражнение
                validation = validator.validate_exercise(joints, exercise_name)
                
                # Кодируем изображение с скелетом для отправки
                _, buffer = cv2.imencode('.jpg', skeleton_image)
                skeleton_base64 = base64.b64encode(buffer).decode('utf-8')
                
                result = {
                    "session_id": session_id,
                    "frame": 0,
                    "status": validation["status"],
                    "feedback": validation["feedback"],
                    "score": validation["score"],
                    "errors": validation["errors"],
                    "joints_detected": visible_joints,
                    "skeleton_image": skeleton_base64  # опционально
                }
            
            # Отправляем результат
            await websocket.send_json(result)
            
    except WebSocketDisconnect:
        print(f"Client disconnected for exercise {exercise_name}")
    except Exception as e:
        print(f"WebSocket error: {e}")