from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# ============================================
# User schemas
# ============================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    diagnosis: Optional[List[str]] = None
    mobility_limits: Optional[List[str]] = None


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    diagnosis: Optional[List[str]] = None
    mobility_limits: Optional[List[str]] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    diagnosis: Optional[List[str]] = None
    mobility_limits: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    user_id: UUID
    email: str
    diagnosis: Optional[List[str]] = None
    mobility_limits: Optional[List[str]] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    diagnosis: Optional[List[str]] = None
    mobility_limits: Optional[List[str]] = None


# ============================================
# Auth schemas
# ============================================

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============================================
# Exercise schemas
# ============================================

class ExerciseResponse(BaseModel):
    id: str = Field(..., description="UUID упражнения")
    title: str
    category: str
    video_url: Optional[str] = None
    duration_sec: Optional[int] = None
    description: Optional[str] = None
    key_points: Optional[List[str]] = None
    is_favorite: int = Field(..., description="1 - в избранном, 0 - не в избранном")

    class Config:
        from_attributes = True


class FavoriteResponse(BaseModel):
    is_favorite: int = 1
    message: str


class CategoryListResponse(BaseModel):
    categories: List[str]


# ============================================
# Progress schemas 
# ============================================

class FrameAnalysis(BaseModel):
    frame_index: int
    joint_name: str
    expected_angle: Optional[float] = None
    actual_angle: Optional[float] = None
    deviation_percent: Optional[float] = None
    error_type: Optional[str] = None
    error_description: Optional[str] = None


class ProgressCreate(BaseModel):
    exercise_id: str  # UUID как строка
    overall_result: str  # "Хорошая работа" или "Есть ошибки"
    recommendation: str
    duration_sec: Optional[int] = None
    frame_analysis: Optional[List[FrameAnalysis]] = None


class ProgressResponse(BaseModel):
    session_id: UUID
    user_id: UUID
    exercise_id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    overall_result: Optional[str] = None
    recommendation: Optional[str] = None
    duration_sec: Optional[int] = None

    class Config:
        from_attributes = True


class FrameAnalysisResponse(BaseModel):
    analysis_id: UUID
    session_id: UUID
    frame_index: int
    joint_name: str
    expected_angle: Optional[float] = None
    actual_angle: Optional[float] = None
    deviation_percent: Optional[float] = None
    error_type: Optional[str] = None
    error_description: Optional[str] = None

    class Config:
        from_attributes = True