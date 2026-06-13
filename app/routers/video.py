"""
Роутер для загрузки и обработки видео
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
import os
import uuid
import shutil

from app.services.video_processor import VideoProcessor

router = APIRouter(prefix="/video", tags=["Video"])

# Инициализация процессора
video_processor = VideoProcessor()

# Папка для временных видео
TEMP_DIR = "temp_videos"
os.makedirs(TEMP_DIR, exist_ok=True)


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Загрузка видео для обработки
    
    Returns:
        task_id для отслеживания статуса
    """
    # Проверяем формат
    if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(400, "Unsupported video format")
    
    # Сохраняем загруженное видео
    task_id = str(uuid.uuid4())[:8]
    input_path = os.path.join(TEMP_DIR, f"input_{task_id}_{file.filename}")
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Запускаем обработку в фоне
    background_tasks.add_task(process_video_background, task_id, input_path)
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": "Video uploaded, processing started"
    }


@router.get("/result/{task_id}")
async def get_result(task_id: str):
    """
    Получение обработанного видео по task_id
    """
    output_path = os.path.join(video_processor.output_dir, f"processed_{task_id}.avi")
    
    if not os.path.exists(output_path):
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Video is still being processed"
        }
    
    return FileResponse(
        output_path,
        media_type="video/x-msvideo",
        filename=f"processed_{task_id}.avi"
    )


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    Проверка статуса обработки видео
    """
    output_path = os.path.join(video_processor.output_dir, f"processed_{task_id}.avi")
    input_path = None
    
    # Ищем входной файл
    for f in os.listdir(TEMP_DIR):
        if task_id in f:
            input_path = os.path.join(TEMP_DIR, f)
            break
    
    if os.path.exists(output_path):
        return {
            "task_id": task_id,
            "status": "completed",
            "message": "Video processed successfully"
        }
    elif input_path and os.path.exists(input_path):
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Video is being processed"
        }
    else:
        return {
            "task_id": task_id,
            "status": "not_found",
            "message": "Task not found"
        }


async def process_video_background(task_id: str, input_path: str):
    """
    Фоновая обработка видео
    """
    print(f"🔄 Processing task {task_id}")
    
    # Обрабатываем видео
    output_path = video_processor.process_video(input_path)
    
    if output_path:
        # Переименовываем с task_id
        final_path = os.path.join(video_processor.output_dir, f"processed_{task_id}.avi")
        if output_path != final_path:
            shutil.move(output_path, final_path)
        print(f"✅ Task {task_id} completed")
    else:
        print(f"❌ Task {task_id} failed")
    
    # Удаляем исходное видео
    try:
        os.remove(input_path)
    except:
        pass