"""
PANDORA Quiz Service Quiz Model
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.question import Question
    from src.models.quiz_session import QuizSession


class QuizStatus(str, Enum):
    """Quiz status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class QuestionType(str, Enum):
    """Question type enumeration."""
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    RANKING = "ranking"


class Quiz(Base, UUIDMixin, TimestampMixin):
    """Quiz model representing a quiz or exam."""
    
    __tablename__ = "quizzes"
    
    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Content
    question_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Settings
    status: Mapped[QuizStatus] = mapped_column(
        String(20),
        default=QuizStatus.DRAFT,
        nullable=False,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        String(30),
        default=QuestionType.MULTIPLE_CHOICE,
        nullable=False,
    )
    
    # Timing
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allowed_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    cooldown_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Scoring
    passing_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    points_per_question: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # Options
    is_adaptive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shuffle_answers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_explanations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_back_navigation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    learning_path_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    difficulty_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Statistics
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Relationships
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="quiz",
        lazy="selectin",
    )
    sessions: Mapped[list["QuizSession"]] = relationship(
        "QuizSession",
        back_populates="quiz",
        lazy="selectin",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_quizzes_status_created", "status", "created_at"),
        Index("ix_quizzes_path_module", "learning_path_id", "module_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Quiz(id={self.id}, title='{self.title}', status={self.status})>"
