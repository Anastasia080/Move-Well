from fastapi import FastAPI, WebSocket, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from app.routers import auth, profile, exercises
from app.websocket_handler import handle_websocket, compare_videos_endpoint, REFERENCE_VIDEOS

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Move Well API...")
    # Создаем папку для эталонных видео если её нет
    os.makedirs("reference_videos", exist_ok=True)
    yield
    print("Shutting down...")

app = FastAPI(
    title="Move Well API",
    description="Rehabilitation app with pose estimation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(exercises.router)

app.mount("/static", StaticFiles(directory="."), name="static")

@app.websocket("/ws/analyze/{exercise}")
async def websocket_endpoint(websocket: WebSocket, exercise: str):
    await handle_websocket(websocket, exercise)

@app.post("/api/compare-videos")
async def compare_videos(
    user_video: UploadFile = File(...),
    exercise: str = Form("general")
):
    """
    Сравнивает видео пользователя с эталонным видео на сервере.
    Эталон выбирается автоматически по типу упражнения.
    """
    return await compare_videos_endpoint(user_video=user_video, exercise=exercise)

@app.get("/api/reference-exercises")
async def get_reference_exercises():
    """Возвращает список упражнений с доступными эталонами"""
    available = []
    for exercise, path in REFERENCE_VIDEOS.items():
        exists = os.path.exists(path)
        available.append({
            "exercise": exercise,
            "has_reference": exists,
            "reference_path": path if exists else None
        })
    
    return JSONResponse({
        "status": "success",
        "exercises": available,
        "total": len(available),
        "available_count": sum(1 for e in available if e["has_reference"])
    })

@app.get("/")
async def root():
    return {
        "message": "Move Well API is running", 
        "status": "ok",
        "endpoints": [
            "/auth/register",
            "/auth/login",
            "/profile",
            "/exercises",
            "/ws/analyze/{exercise}",
            "/api/compare-videos",
            "/api/reference-exercises"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}