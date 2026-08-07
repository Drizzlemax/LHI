"""
PANDORA Learning Service - Path Lesson Models
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.module import Module
    from src.models.progress import UserProgress


class LessonStatus(str, enum.Enum):
    """Lesson status enumeration."""
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class LessonType(str, enum.Enum):
    """Lesson type enumeration."""
    VIDEO = "video"
    ARTICLE = "article"
    QUIZ = "quiz"
    ASSIGNMENT = "assignment"
    PROJECT = "project"
    LIVE_SESSION = "live_session"
    INTERACTIVE = "interactive"
    EXAM = "exam"


class PathLesson(Base):
    """
    Path Lesson model representing a content item within a module.
    
    Lessons are the atomic units of learning that can include videos,
    articles, quizzes, assignments, or interactive content.
    """
    __tablename__ = "path_lessons"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Core fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    lesson_type: Mapped[LessonType] = mapped_column(
        SQLEnum(LessonType, name="lesson_type"),
        default=LessonType.ARTICLE,
        nullable=False,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Status
    status: Mapped[LessonStatus] = mapped_column(
        SQLEnum(LessonStatus, name="lesson_status"),
        default=LessonStatus.LOCKED,
        nullable=False,
        index=True,
    )
    
    # Content metadata
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Prerequisites - stored as JSON
    prerequisite_ids: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Content configuration
    content_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # {
    #     "video_url": "...",
    #     "article_content": "...",
    #     "quiz_id": "...",
    #     "quiz_config": {...}
    # }
    
    # Completion requirements
    completion_requirements: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    # {
    #     "min_time_seconds": 300,
    #     "quiz_passing_score": 70,
    #     "requires_submission": true
    # }
    
    # Settings
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_preview: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bonus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_replay: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
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
    unlocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    module: Mapped["Module"] = relationship(
        "Module",
        back_populates="lessons",
    )
    user_progress: Mapped[list["UserProgress"]] = relationship(
        "UserProgress",
        back_populates="lesson",
        cascade="all, delete-orphan",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_path_lessons_module_order", "module_id", "order_index"),
        Index("ix_path_lessons_content", "content_id"),
        UniqueConstraint("module_id", "order_index", name="uq_path_lessons_module_order"),
    )
    
    def __repr__(self) -> str:
        return f"<PathLesson(id={self.id}, title='{self.title}', type={self.lesson_type})>"
