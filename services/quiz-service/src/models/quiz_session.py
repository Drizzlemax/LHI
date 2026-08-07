"""
PANDORA Quiz Service Quiz Session Model
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.quiz import Quiz
    from src.models.response import QuestionResponse


class QuizSessionStatus(str, Enum):
    """Quiz session status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"


class QuizSession(Base, UUIDMixin, TimestampMixin):
    """Quiz session model representing a user's attempt at a quiz."""
    
    __tablename__ = "quiz_sessions"
    
    # Quiz reference
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    
    # Session state
    status: Mapped[QuizSessionStatus] = mapped_column(
        String(20),
        default=QuizSessionStatus.NOT_STARTED,
        nullable=False,
    )
    
    # Questions in this session (ordered)
    question_ids: Mapped[list[uuid.UUID]] = mapped_column(
        JSON,
        nullable=False,
    )
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Scoring
    raw_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentage_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    scaled_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    
    # IRT parameters
    estimated_ability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ability_std: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # Adaptive selection info
    selection_history: Mapped[list[dict] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    response_history: Mapped[list[dict] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Navigation
    answered_questions: Mapped[list[uuid.UUID] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    flagged_questions: Mapped[list[uuid.UUID] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Feedback
    feedback_provided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanations_shown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    quiz: Mapped["Quiz"] = relationship(
        "Quiz",
        back_populates="sessions",
    )
    responses: Mapped[list["QuestionResponse"]] = relationship(
        "QuestionResponse",
        back_populates="session",
        lazy="selectin",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_quiz_sessions_user_quiz", "user_id", "quiz_id"),
        Index("ix_quiz_sessions_status", "status"),
        Index("ix_quiz_sessions_started", "started_at"),
    )
    
    def __repr__(self) -> str:
        return f"<QuizSession(id={self.id}, user={self.user_id}, status={self.status})>"
    
    @property
    def is_timed_out(self) -> bool:
        """Check if session has exceeded time limit."""
        if self.started_at and self.time_limit_minutes:
            elapsed = datetime.now(self.started_at.tzinfo) - self.started_at
            return elapsed.total_seconds() > (self.time_limit_minutes * 60)
        return False
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.question_ids:
            return (self.current_question_index / len(self.question_ids)) * 100
        return 0.0
