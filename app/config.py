from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost/movewell"
    
    # Redis (опционально)
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
    
    # S3 / MinIO (опционально)
    S3_ENDPOINT: Optional[str] = "localhost:9000"
    S3_ACCESS_KEY: Optional[str] = "minioadmin"
    S3_SECRET_KEY: Optional[str] = "minioadmin"
    S3_BUCKET_VIDEOS: Optional[str] = "exercise-videos"
    S3_USE_SSL: bool = False
    
    # MediaPipe
    POSE_DETECTION_CONFIDENCE: float = 0.5
    POSE_TRACKING_CONFIDENCE: float = 0.5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()