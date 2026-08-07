"""
PANDORA Quiz Service Question Response Model
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.question import Question
    from src.models.quiz_session import QuizSession


class QuestionResponse(Base, UUIDMixin, TimestampMixin):
    """Question response model representing a user's answer to a question."""
    
    __tablename__ = "question_responses"
    
    # References
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Response data
    user_answer: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Example: {"type": "single", "value": "a"} or {"type": "text", "value": "answer text"}
    
    # Correctness
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    partial_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Timing
    question_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Position in quiz
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # IRT data
    ability_at_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_at_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Review data
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    was_changed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Feedback
    feedback: Mapped[str | None] = mapped_column(String(500), nullable=True)
    explanation_shown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    session: Mapped["QuizSession"] = relationship(
        "QuizSession",
        back_populates="responses",
    )
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="responses",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_question_responses_session", "session_id"),
        Index("ix_question_responses_question", "question_id"),
        Index("ix_question_responses_session_question", "session_id", "question_id", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<QuestionResponse(id={self.id}, correct={self.is_correct})>"
    
    @property
    def time_taken(self) -> int | None:
        """Calculate time taken to answer in seconds."""
        if self.question_started_at and self.answered_at:
            delta = self.answered_at - self.question_started_at
            return int(delta.total_seconds())
        return None
