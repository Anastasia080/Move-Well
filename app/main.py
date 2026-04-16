from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import auth, profile, exercises, websocket

from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Move Well API...")
    yield
    print("Shutting down...")

app = FastAPI(
    title="Move Well API",
    description="Rehabilitation app with pose estimation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)      # /auth/register, /auth/login
app.include_router(profile.router)   # /profile (GET, POST, PUT, DELETE)
app.include_router(exercises.router) # /exercises (GET, POST, DELETE, favorites)
app.include_router(websocket.router) 

# Для отдачи HTML файла
app.mount("/static", StaticFiles(directory="."), name="static")

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
            "/exercises/favorites/list",
            "/exercises/categories/list"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}