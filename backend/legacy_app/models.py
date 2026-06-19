from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    diagnosis = Column(ARRAY(Text), default=[])
    mobility_limits = Column(ARRAY(Text), default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("SessionProgress", back_populates="user", cascade="all, delete-orphan")


class Exercise(Base):
    __tablename__ = "exercises"

    exercise_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    video_url = Column(String(500), nullable=True)
    duration_sec = Column(Integer, nullable=True)
    key_points = Column(ARRAY(Text), default=[])
    difficulty = Column(Integer, nullable=True)
    mobility_level = Column(Integer, nullable=True)

    # Связи
    favorites = relationship("Favorite", back_populates="exercise", cascade="all, delete-orphan")
    metrics = relationship("ExerciseMetric", back_populates="exercise", cascade="all, delete-orphan")
    sessions = relationship("SessionProgress", back_populates="exercise", cascade="all, delete-orphan")


class ExerciseMetric(Base):
    __tablename__ = "exercise_metrics"

    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.exercise_id", ondelete="CASCADE"), nullable=False)
    frame_index = Column(Integer, nullable=False)
    joint_name = Column(String(50), nullable=False)
    joint_from = Column(String(50), nullable=True)
    joint_to = Column(String(50), nullable=True)
    joint_ref = Column(String(50), nullable=True)
    angle_min = Column(Integer, nullable=True)  # DECIMAL(5,2) в БД
    angle_max = Column(Integer, nullable=True)  # DECIMAL(5,2) в БД
    distance_min = Column(Integer, nullable=True)  # DECIMAL(5,2) в БД
    distance_max = Column(Integer, nullable=True)  # DECIMAL(5,2) в БД
    description = Column(Text, nullable=True)

    # Связи
    exercise = relationship("Exercise", back_populates="metrics")


class Favorite(Base):
    __tablename__ = "favorites"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.exercise_id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи
    user = relationship("User", back_populates="favorites")
    exercise = relationship("Exercise", back_populates="favorites")


class SessionProgress(Base):
    __tablename__ = "session_progress"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.exercise_id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    overall_result = Column(String(50), nullable=True)
    recommendation = Column(String(255), nullable=True)
    duration_sec = Column(Integer, nullable=True)

    # Связи
    user = relationship("User", back_populates="sessions")
    exercise = relationship("Exercise", back_populates="sessions")
    frame_analyses = relationship("SessionFrameAnalysis", back_populates="session", cascade="all, delete-orphan")


class SessionFrameAnalysis(Base):
    __tablename__ = "session_frame_analysis"

    analysis_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("session_progress.session_id", ondelete="CASCADE"), nullable=False)
    frame_index = Column(Integer, nullable=False)
    joint_name = Column(String(50), nullable=False)
    expected_angle = Column(Integer, nullable=True)  # DECIMAL(5,2) в БД
    actual_angle = Column(Integer, nullable=True)    # DECIMAL(5,2) в БД
    deviation_percent = Column(Integer, nullable=True)  # DECIMAL(5,2) в БД
    error_type = Column(String(100), nullable=True)
    error_description = Column(Text, nullable=True)

    # Связи
    session = relationship("SessionProgress", back_populates="frame_analyses")