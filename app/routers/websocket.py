from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import cv2
import base64
import json
import numpy as np
from datetime import datetime
import uuid
import asyncio

from app.database import get_db
from app.models import User, SessionProgress, SessionFrameAnalysis
from app.auth_utils import get_current_user_ws
from app.services.pose_analyzer import PoseAnalyzer
from app.services.openpose_integration import OpenPoseIntegration

router = APIRouter(tags=["WebSocket"])

# Инициализация сервисов OpenPose
openpose = OpenPoseIntegration(r"D:\openpose\openpose")
#pose_analyzer = PoseAnalyzer(openpose_path=r"D:\openpose\openpose")
#pose_analyzer.start()

# Простой валидатор упражнений (без отдельного файла)
class SimpleValidator:
    """Простой валидатор упражнений"""
    
    def validate_exercise(self, joints, exercise_name):
        """Проверка выполнения упражнения"""
        visible_joints = sum(1 for j in joints if j is not None)
        
        if visible_joints < 5:
            return {
                "status": "no_person",
                "feedback": "Встаньте в кадр полностью",
                "score": 0,
                "errors": [{"error": "Недостаточно ключевых точек"}]
            }
        
        # Базовая проверка для приседаний
        if exercise_name == "squat":
            # Проверяем углы коленей (индексы 9 и 12 - колени)
            left_knee = joints[12] if 12 < len(joints) else None
            right_knee = joints[9] if 9 < len(joints) else None
            
            errors = []
            
            if left_knee and right_knee:
                # Если колени высоко (y маленький) - приседание неглубокое
                if left_knee.y < 200 and right_knee.y < 200:
                    errors.append({"error": "Приседайте глубже", "severity": "medium"})
                else:
                    errors.append({"error": "Хороший угол в коленях", "severity": "low"})
            
            if len(errors) == 0 or (len(errors) == 1 and errors[0]["severity"] == "low"):
                status = "good"
                feedback = "Отлично! Приседание выполнено правильно"
                score = 85
            else:
                status = "needs_improvement"
                feedback = "Хорошо, но приседайте глубже"
                score = 60
                
        elif exercise_name == "pushup":
            status = "good"
            feedback = "Хорошая работа! Продолжайте"
            score = 80
        else:
            status = "good"
            feedback = f"Упражнение {exercise_name} выполняется"
            score = 75
        
        return {
            "status": status,
            "feedback": feedback,
            "score": score,
            "errors": errors
        }


validator = SimpleValidator()


@router.websocket("/ws/analyze/{exercise_name}")
async def websocket_analyze(
    websocket: WebSocket,
    exercise_name: str
):
    """WebSocket для анализа выполнения упражнений"""
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    frame_count = 0
    all_errors = []
    
    try:
        # Получаем токен авторизации (опционально)
        init_data = await websocket.receive_text()
        init_json = json.loads(init_data)
        token = init_json.get("token")
        
        print(f"Session started: {session_id}, exercise: {exercise_name}")
        print(f"Token: {token[:50]}..." if token else "No token provided")
        
        # Основной цикл обработки кадров
        while True:
            # Получаем кадр от клиента
            data = await websocket.receive_text()
            frame_data = json.loads(data)
            
            if "image" not in frame_data:
                continue
            
            # Декодируем изображение из base64
            try:
                image_bytes = base64.b64decode(frame_data["image"])
                np_arr = np.frombuffer(image_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    await websocket.send_json({"error": "Не удалось декодировать изображение"})
                    continue
                    
            except Exception as e:
                print(f"Error decoding image: {e}")
                await websocket.send_json({"error": f"Ошибка декодирования: {str(e)}"})
                continue
            
            frame_count += 1
            
            # Анализируем позу через OpenPose
            try:
                joints, skeleton_image = pose_analyzer.analyze_image(frame)
            except Exception as e:
                print(f"Pose analysis error: {e}")
                joints = [None] * 19
                skeleton_image = frame
            
            # Подсчитываем видимые суставы
            visible_joints = sum(1 for j in joints if j is not None)
            print(f"Frame {frame_count}: Visible joints: {visible_joints}/18")
            
            # Проверяем выполнение упражнения
            if visible_joints < 5:
                result = {
                    "session_id": session_id,
                    "frame": frame_count,
                    "status": "no_person",
                    "feedback": "Пользователь не обнаружен. Встаньте в кадр, чтобы вас было видно полностью",
                    "score": 0,
                    "errors": [{"error": "Человек не обнаружен в кадре"}],
                    "joints_detected": visible_joints,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Валидируем упражнение
                validation = validator.validate_exercise(joints, exercise_name)
                
                # Сохраняем ошибки для истории
                for error in validation.get("errors", []):
                    all_errors.append({
                        "frame": frame_count,
                        "error": error.get("error", ""),
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Кодируем изображение с скелетом для отправки (опционально)
                _, buffer = cv2.imencode('.jpg', skeleton_image)
                skeleton_base64 = base64.b64encode(buffer).decode('utf-8')
                
                result = {
                    "session_id": session_id,
                    "frame": frame_count,
                    "status": validation["status"],
                    "feedback": validation["feedback"],
                    "score": validation["score"],
                    "errors": validation.get("errors", []),
                    "joints_detected": visible_joints,
                    "skeleton_image": skeleton_base64,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Отправляем результат клиенту
            try:
                await websocket.send_json(result)
            except Exception as e:
                print(f"Error sending response: {e}")
                break
            
            # Небольшая задержка для контроля частоты кадров
            await asyncio.sleep(0.05)
            
    except WebSocketDisconnect:
        print(f"Client disconnected for exercise {exercise_name}")
        
        # Сохраняем результаты сессии (опционально)
        print(f"Session {session_id} completed with {frame_count} frames processed")
        print(f"Total errors detected: {len(all_errors)}")
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


@router.websocket("/ws/test")
async def websocket_test(
    websocket: WebSocket
):
    """Простой тестовый WebSocket для проверки соединения"""
    await websocket.accept()
    print("Test WebSocket connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received: {data}")
            await websocket.send_json({"message": f"Echo: {data}", "timestamp": datetime.now().isoformat()})
    except WebSocketDisconnect:
        print("Test WebSocket disconnected")