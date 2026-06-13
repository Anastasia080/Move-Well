from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models import Exercise, Favorite, User
from app.schemas import ExerciseResponse, FavoriteResponse, CategoryListResponse
from app.auth_utils import get_current_user

router = APIRouter(prefix="/exercises", tags=["Exercises"])


@router.get("/", response_model=List[ExerciseResponse])
async def get_exercises(
    category: Optional[str] = Query(None, description="Фильтр по категории: arms/legs/core/chest/breathing"),
    search: Optional[str] = Query(None, description="Поиск по названию упражнения"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список всех упражнений.
    - Поддерживает фильтрацию по категории
    - Поддерживает поиск по названию
    - Показывает, добавлено ли упражнение в избранное у текущего пользователя
    """
    # Базовый запрос
    query = select(Exercise)
    
    # Фильтр по категории
    if category:
        query = query.where(Exercise.category == category)
    
    # Поиск по названию
    if search:
        query = query.where(Exercise.title.ilike(f"%{search}%"))
    
    # Сортировка по названию
    query = query.order_by(Exercise.title)
    
    result = await db.execute(query)
    exercises = result.scalars().all()
    
    # Получаем список избранных упражнений текущего пользователя
    favorites_result = await db.execute(
        select(Favorite.exercise_id).where(Favorite.user_id == current_user.user_id)
    )
    favorite_ids = {row[0] for row in favorites_result.all()}
    
    # Формируем ответ с is_favorite
    response = []
    for ex in exercises:
        response.append(ExerciseResponse(
            id=str(ex.exercise_id),
            title=ex.title,
            category=ex.category,
            video_url=ex.video_url,
            duration_sec=ex.duration_sec,
            description=ex.description,
            key_points=ex.key_points if ex.key_points else [],
            is_favorite=1 if ex.exercise_id in favorite_ids else 0
        ))
    
    return response


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise_detail(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить детальную информацию о конкретном упражнении по его ID.
    """
    # Пробуем преобразовать строку в UUID
    try:
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid exercise ID format"
        )
    
    # Ищем упражнение
    result = await db.execute(
        select(Exercise).where(Exercise.exercise_id == exercise_uuid)
    )
    exercise = result.scalar_one_or_none()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    
    # Проверяем, в избранном ли упражнение у пользователя
    fav_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.user_id,
            Favorite.exercise_id == exercise_uuid
        )
    )
    is_favorite = fav_result.scalar_one_or_none() is not None
    
    return ExerciseResponse(
        id=str(exercise.exercise_id),
        title=exercise.title,
        category=exercise.category,
        video_url=exercise.video_url,
        duration_sec=exercise.duration_sec,
        description=exercise.description,
        key_points=exercise.key_points if exercise.key_points else [],
        is_favorite=1 if is_favorite else 0
    )


@router.post("/{exercise_id}/favorite", response_model=FavoriteResponse, status_code=status.HTTP_200_OK)
async def add_to_favorites(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Добавить упражнение в избранное.
    """
    # Проверяем корректность UUID
    try:
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid exercise ID format"
        )
    
    # Проверяем, существует ли упражнение
    exercise_result = await db.execute(
        select(Exercise).where(Exercise.exercise_id == exercise_uuid)
    )
    if not exercise_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    
    # Проверяем, не добавлено ли уже в избранное
    existing = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.user_id,
            Favorite.exercise_id == exercise_uuid
        )
    )
    if existing.scalar_one_or_none():
        return FavoriteResponse(
            is_favorite=1,
            message="Упражнение уже в избранном"
        )
    
    # Добавляем в избранное
    favorite = Favorite(
        user_id=current_user.user_id,
        exercise_id=exercise_uuid
    )
    db.add(favorite)
    await db.commit()
    
    return FavoriteResponse(
        is_favorite=1,
        message="Упражнение добавлено в избранное"
    )


@router.delete("/{exercise_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    exercise_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удалить упражнение из избранного.
    """
    # Проверяем корректность UUID
    try:
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid exercise ID format"
        )
    
    # Удаляем из избранного
    result = await db.execute(
        delete(Favorite).where(
            Favorite.user_id == current_user.user_id,
            Favorite.exercise_id == exercise_uuid
        )
    )
    await db.commit()
    
    # Если ничего не удалили, упражнения и не было в избранном - это не ошибка
    return None


@router.get("/favorites/list", response_model=List[ExerciseResponse])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список всех упражнений, добавленных пользователем в избранное.
    """
    result = await db.execute(
        select(Exercise)
        .join(Favorite, Exercise.exercise_id == Favorite.exercise_id)
        .where(Favorite.user_id == current_user.user_id)
        .order_by(Favorite.added_at.desc())
    )
    exercises = result.scalars().all()
    
    return [
        ExerciseResponse(
            id=str(ex.exercise_id),
            title=ex.title,
            category=ex.category,
            video_url=ex.video_url,
            duration_sec=ex.duration_sec,
            description=ex.description,
            key_points=ex.key_points if ex.key_points else [],
            is_favorite=1  # В этом списке все упражнения - избранные
        )
        for ex in exercises
    ]


@router.get("/categories/list", response_model=CategoryListResponse)
async def get_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список всех уникальных категорий упражнений.
    """
    result = await db.execute(select(Exercise.category).distinct())
    categories = result.scalars().all()
    
    return CategoryListResponse(categories=categories)