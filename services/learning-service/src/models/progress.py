"""
PANDORA Learning Service - User Progress Models
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    JSON,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.path_lesson import PathLesson


class ProgressStatus(str, enum.Enum):
    """User progress status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class UserProgress(Base):
    """
    User Progress model tracking individual lesson progress.
    
    Records user interactions with lessons including completion status,
    quiz results, time spent, and other engagement metrics.
    """
    __tablename__ = "user_progress"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("path_lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    learning_path_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Status
    status: Mapped[ProgressStatus] = mapped_column(
        SQLEnum(ProgressStatus, name="progress_status"),
        default=ProgressStatus.NOT_STARTED,
        nullable=False,
        index=True,
    )
    
    # Progress tracking
    progress_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Time tracking
    time_spent_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_position_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    
    # Quiz results (if applicable)
    quiz_results: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    # {
    #     "quiz_id": "...",
    #     "score": 85.0,
    #     "passed": true,
    #     "answers": [...],
    #     "time_spent_seconds": 1200
    # }
    
    # Score and grading
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    points_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Completion details
    completion_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    # "manual", "quiz_passed", "time_threshold", "submission_approved"
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    lesson: Mapped["PathLesson"] = relationship(
        "PathLesson",
        back_populates="user_progress",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_user_progress_user_lesson", "user_id", "lesson_id", unique=True),
        Index("ix_user_progress_user_path", "user_id", "learning_path_id"),
        Index("ix_user_progress_user_module", "user_id", "module_id"),
        Index("ix_user_progress_status", "status", "user_id"),
    )
    
    def __repr__(self) -> str:
        return f"<UserProgress(id={self.id}, user_id={self.user_id}, lesson={self.lesson_id}, status={self.status})>"


class UserLearningStats(Base):
    """
    Aggregated learning statistics per user.
    
    Stores computed statistics about user learning activity
    for quick access without expensive aggregations.
    """
    __tablename__ = "user_learning_stats"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Activity counts
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quizzes_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quizzes_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    paths_enrolled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    paths_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Time metrics
    total_time_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Scores
    average_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    highest_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Badges/achievements
    badges: Mapped[list[str] | None] = mapped_column(nullable=True)
    achievements: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    def __repr__(self) -> str:
        return f"<UserLearningStats(user_id={self.user_id}, xp={self.total_xp})>"


class LearningPathEnrollment(Base):
    """
    Learning path enrollment records.
    
    Tracks which users are enrolled in which learning paths
    and their enrollment status.
    """
    __tablename__ = "learning_path_enrollments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    learning_path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Enrollment details
    enrolled_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    enrollment_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    # "direct", "course", "recommendation", "admin"
    
    # Progress
    progress_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    current_module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    current_lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completion_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Timestamps
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    unenrolled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_enrollments_user_path", "user_id", "learning_path_id", unique=True),
        Index("ix_enrollments_path_active", "learning_path_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<LearningPathEnrollment(user_id={self.user_id}, path={self.learning_path_id})>"
