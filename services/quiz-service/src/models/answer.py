"""
PANDORA Quiz Service Answer Model
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.attempt import AssessmentAttempt
    from src.models.question import AssessmentQuestion


class Answer(Base, UUIDMixin, TimestampMixin):
    """Answer model representing a user's answer to an assessment question.
    
    Stores the user's response to a question, including timing,
    correctness, and scoring information.
    """
    
    __tablename__ = "answers"
    
    # References
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Answer content
    answer: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Example formats:
    # - Single choice: {"type": "single", "value": "a"}
    # - Multiple choice: {"type": "multiple", "values": ["a", "c"]}
    # - Text: {"type": "text", "value": "user's answer"}
    # - Fill in blank: {"type": "fill_blank", "values": ["word1", "word2"]}
    
    # Correctness
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    partial_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Points
    points_earned: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
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
    
    # Position in assessment
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Navigation state
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    was_changed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Review state
    explanation_shown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    correct_answer_shown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Manual grading (for essay, etc.)
    is_graded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    graded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    grading_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Feedback
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Relationships
    attempt: Mapped["AssessmentAttempt"] = relationship(
        "AssessmentAttempt",
        back_populates="answers",
    )
    question: Mapped["AssessmentQuestion"] = relationship(
        "AssessmentQuestion",
        back_populates="answers",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_answers_attempt", "attempt_id"),
        Index("ix_answers_question", "question_id"),
        Index("ix_answers_attempt_question", "attempt_id", "question_id", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<Answer(id={self.id}, attempt={self.attempt_id}, correct={self.is_correct})>"
    
    @property
    def time_taken(self) -> int | None:
        """Calculate the time taken to answer in seconds."""
        if self.question_started_at and self.answered_at:
            return int((self.answered_at - self.question_started_at).total_seconds())
        return None
    
    @property
    def score_percentage(self) -> float | None:
        """Calculate the score as a percentage."""
        if self.max_points > 0:
            return (self.points_earned / self.max_points) * 100
        return None
    
    def mark_correct(self, points_earned: float = 0.0) -> None:
        """Mark the answer as correct."""
        self.is_correct = True
        self.points_earned = points_earned
        self.is_graded = True
    
    def mark_incorrect(self) -> None:
        """Mark the answer as incorrect."""
        self.is_correct = False
        self.points_earned = 0.0
        self.is_graded = True
    
    def mark_skipped(self) -> None:
        """Mark the answer as skipped."""
        self.is_skipped = True
        self.answer = None
