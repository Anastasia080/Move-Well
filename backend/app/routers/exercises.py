import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.models import Exercise, Favorite, User
from app.schemas import ExerciseResponse, FavoriteResponse, CategoryListResponse
from app.auth_utils import get_current_user
from app.services.pose_analyzer import PoseAnalyzer
from app.services.video_analyzer import VideoAnalyzer, MockVideoAnalyzer, get_reference_video_path

_pose_analyzer: PoseAnalyzer | None = None
_video_analyzer = None  # VideoAnalyzer | MockVideoAnalyzer

def _get_video_analyzer():
    global _pose_analyzer, _video_analyzer
    if _video_analyzer is None:
        try:
            _pose_analyzer = PoseAnalyzer()
            _video_analyzer = VideoAnalyzer(_pose_analyzer)
            print("PoseAnalyzer ready: using OpenPose VideoAnalyzer")
        except Exception as e:
            print(f"OpenPose недоступен ({e}), используется MockVideoAnalyzer")
            _video_analyzer = MockVideoAnalyzer()
    return _video_analyzer

DIAGNOSIS_RESTRICTIONS = {
    "Артрит":               {"max_difficulty": 1, "exclude_categories": []},
    "Артроз":               {"max_difficulty": 1, "exclude_categories": []},
    "Остеопороз":           {"max_difficulty": 0, "exclude_categories": []},
    "Сколиоз":              {"max_difficulty": 1, "exclude_categories": ["body"]},
    "Межпозвоночная грыжа": {"max_difficulty": 0, "exclude_categories": ["body"]},
    "Последствия травм":    {"max_difficulty": 1, "exclude_categories": []},
}

LIMIT_RESTRICTIONS = {
    "Ограничение подвижности плеча":                  ["hands"],
    "Ограничение подвижности колена":                 ["legs"],
    "Ограничение подвижности тазобедренного сустава": ["legs"],
    "Ограничение подвижности позвоночника":           ["body"],
    "Ограничение подвижности локтя":                  ["hands"],
    "Ограничение подвижности запястья":               ["hands"],
}

MOBILITY_LEVEL_MAP = {"Низкий": 0, "Средний": 1, "Высокий": 2}

router = APIRouter(prefix="/exercises", tags=["Exercises"])

@router.get("/recommended", response_model=List[ExerciseResponse])
async def get_recommended_exercises(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    max_difficulty = 2
    excluded_categories: set = set()

    for diagnosis in (current_user.diagnosis or []):
        if diagnosis in DIAGNOSIS_RESTRICTIONS:
            r = DIAGNOSIS_RESTRICTIONS[diagnosis]
            max_difficulty = min(max_difficulty, r["max_difficulty"])
            excluded_categories.update(r["exclude_categories"])

    for limit in (current_user.mobility_limits or []):
        if limit in LIMIT_RESTRICTIONS:
            excluded_categories.update(LIMIT_RESTRICTIONS[limit])

    mobility_value = 2
    for limit in (current_user.mobility_limits or []):
        if limit in MOBILITY_LEVEL_MAP:
            mobility_value = MOBILITY_LEVEL_MAP[limit]
            break

    query = select(Exercise)

    if excluded_categories:
        query = query.where(Exercise.category.notin_(excluded_categories))

    strict_query = query.where(
        (Exercise.difficulty == None) | (Exercise.difficulty <= max_difficulty)
    ).where(
        (Exercise.mobility_level == None) | (Exercise.mobility_level <= mobility_value)
    ).order_by(Exercise.title)

    result = await db.execute(strict_query)
    exercises_list = result.scalars().all()

    # Если строгий фильтр дал пустой список — показываем наиболее простые упражнения
    # из допустимых категорий, отсортированные по сложности
    if not exercises_list:
        fallback_query = query.order_by(Exercise.difficulty, Exercise.mobility_level, Exercise.title)
        result = await db.execute(fallback_query)
        exercises_list = result.scalars().all()

    favorites_result = await db.execute(
        select(Favorite.exercise_id).where(Favorite.user_id == current_user.user_id)
    )
    favorite_ids = {row[0] for row in favorites_result.all()}

    return [
        ExerciseResponse(
            id=str(ex.exercise_id),
            title=ex.title,
            category=ex.category,
            video_url=ex.video_url,
            duration_sec=ex.duration_sec,
            description=ex.description,
            key_points=ex.key_points if ex.key_points else [],
            is_favorite=1 if ex.exercise_id in favorite_ids else 0
        )
        for ex in exercises_list
    ]

@router.get("", response_model=List[ExerciseResponse])
@router.get("/", response_model=List[ExerciseResponse])
async def get_exercises(
    category: Optional[str] = Query(None, description="Фильтр по категории: arms/legs/core/chest/breathing"),
    search: Optional[str] = Query(None, description="Поиск по названию упражнения"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Exercise)
    if category:
        query = query.where(Exercise.category == category)
    if search:
        query = query.where(Exercise.title.ilike(f"%{search}%"))
    query = query.order_by(Exercise.title)
    result = await db.execute(query)
    exercises = result.scalars().all()
    favorites_result = await db.execute(
        select(Favorite.exercise_id).where(Favorite.user_id == current_user.user_id)
    )
    favorite_ids = {row[0] for row in favorites_result.all()}
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
    try:
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid exercise ID format"
        )
    result = await db.execute(
        select(Exercise).where(Exercise.exercise_id == exercise_uuid)
    )
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
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
    try:
        exercise_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid exercise ID format"
        )
    exercise_result = await db.execute(
        select(Exercise).where(Exercise.exercise_id == exercise_uuid)
    )
    if not exercise_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
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
    result = await db.execute(select(Exercise.category).distinct())
    categories = result.scalars().all()
    return CategoryListResponse(categories=categories)


@router.post("/{exercise_id}/analyze")
async def analyze_user_video(
    exercise_id: str,
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Принимает видео пользователя, сравнивает с эталонным.
    Использует OpenPose если доступен, иначе — анализ движения по кадрам.
    Возвращает score (0-100) и список ошибок по суставам.
    """
    analyzer = _get_video_analyzer()

    # Загружаем упражнение из БД
    try:
        ex_uuid = UUID(exercise_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID упражнения")

    result = await db.execute(select(Exercise).where(Exercise.exercise_id == ex_uuid))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="Упражнение не найдено")

    # Сохраняем видео пользователя во временный файл
    suffix = os.path.splitext(video.filename or '.mp4')[1] or '.mp4'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await video.read())
        user_video_path = tmp.name

    try:
        # Извлекаем углы из видео пользователя
        user_frames = analyzer.extract_angles_from_video(user_video_path)
        if not user_frames:
            return {"score": 0, "errors": [{"joint": "Видео", "message": "Не удалось обнаружить позу на видео. Убедитесь, что вы полностью в кадре."}], "frames_analyzed": 0}

        # Ищем эталонное видео
        ref_path = get_reference_video_path(exercise_id, exercise.video_url)
        if ref_path is None:
            # Нет эталона — возвращаем базовую оценку по видимости суставов
            n_joints = len(getattr(getattr(analyzer, 'analyzer', None), 'JOINT_NAMES', {})) or 7
            avg_joints = sum(len(f) for f in user_frames) / len(user_frames) if user_frames else 0
            score = min(100, int(avg_joints / n_joints * 100 * 2))
            return {
                "score": score,
                "errors": [{"joint": "Эталон", "message": "Эталонное видео не найдено, оценка по качеству позы"}],
                "frames_analyzed": len(user_frames)
            }

        # Загружаем или извлекаем эталонные углы (кэшируется)
        ref_frames = analyzer.get_reference_angles(exercise_id, ref_path)
        if not ref_frames:
            return {"score": 0, "errors": [{"joint": "Эталон", "message": "Не удалось обработать эталонное видео"}], "frames_analyzed": 0}

        # Сравниваем
        score, errors = analyzer.compare(ref_frames, user_frames)
        return {
            "score": score,
            "errors": errors,
            "frames_analyzed": len(user_frames),
            "reference_frames": len(ref_frames)
        }

    finally:
        os.unlink(user_video_path)