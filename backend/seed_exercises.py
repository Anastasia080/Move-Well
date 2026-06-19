import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Exercise

exercises_data = [
    {
        "title": "Упражнения для корпуса",
        "description": "Комплекс упражнений для укрепления мышц корпуса, улучшения осанки и гибкости позвоночника.",
        "category": "body",
        "video_url": "sample_body.mp4",
        "duration_sec": 180,
        "key_points": [],
        "difficulty": 1,
        "mobility_level": 1
    },
    {
        "title": "Упражнения для рук",
        "description": "Упражнения для разработки плечевых суставов, укрепления мышц рук и улучшения подвижности.",
        "category": "hands",
        "video_url": "sample_hands.mp4",
        "duration_sec": 120,
        "key_points": [],
        "difficulty": 1,
        "mobility_level": 1
    },
    {
        "title": "Упражнения для ног",
        "description": "Комплекс упражнений для укрепления мышц ног, улучшения подвижности коленных и тазобедренных суставов.",
        "category": "legs",
        "video_url": "sample_legs.mp4",
        "duration_sec": 150,
        "key_points": [],
        "difficulty": 1,
        "mobility_level": 1
    },
]

async def seed_exercises():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        from sqlalchemy import select, delete
        # Удаляем все существующие упражнения
        await session.execute(delete(Exercise))
        await session.commit()
        # Добавляем новые упражнения
        for data in exercises_data:
            exercise = Exercise(
                exercise_id=uuid.uuid4(),
                title=data["title"],
                description=data["description"],
                category=data["category"],
                video_url=data["video_url"],
                duration_sec=data["duration_sec"],
                key_points=data["key_points"],
                difficulty=data["difficulty"],
                mobility_level=data["mobility_level"]
            )
            session.add(exercise)
        await session.commit()
        print(f"Добавлено {len(exercises_data)} упражнений в базу данных!")

if __name__ == "__main__":
    asyncio.run(seed_exercises())
