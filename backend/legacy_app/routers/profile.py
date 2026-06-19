from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.database import get_db
from app.models import User
from app.schemas import ProfileResponse, ProfileUpdate
from app.auth_utils import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить профиль текущего пользователя"""
    return ProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        diagnosis=current_user.diagnosis,
        mobility_limits=current_user.mobility_limits,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.put("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить профиль пользователя"""
    update_data = {}
    if profile_data.diagnosis is not None:
        update_data["diagnosis"] = profile_data.diagnosis
    if profile_data.mobility_limits is not None:
        update_data["mobility_limits"] = profile_data.mobility_limits
    
    if update_data:
        await db.execute(
            update(User)
            .where(User.user_id == current_user.user_id)
            .values(**update_data)
        )
        await db.commit()
        await db.refresh(current_user)
    
    return ProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        diagnosis=current_user.diagnosis,
        mobility_limits=current_user.mobility_limits,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    confirmation: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить аккаунт (требуется подтверждение)"""
    if not confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please confirm account deletion with confirmation=true"
        )
    
    await db.execute(delete(User).where(User.user_id == current_user.user_id))
    await db.commit()

@router.get("/diagnosis")  # GET /profile/diagnosis
async def get_my_diagnosis(current_user: User = Depends(get_current_user)):
    """Получить только диагноз и ограничения"""
    return {
        "diagnosis": current_user.diagnosis,
        "mobility_limits": current_user.mobility_limits
    }