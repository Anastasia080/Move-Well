from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import auth, profile, exercises
from app.routers import websocket
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(exercises.router)
app.include_router(websocket.router)

app.mount("/static", StaticFiles(directory="."), name="static")
app.mount("/videos", StaticFiles(directory="static/videos"), name="videos")

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
