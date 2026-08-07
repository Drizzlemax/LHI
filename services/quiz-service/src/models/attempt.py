"""
PANDORA Quiz Service Assessment Attempt Model
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.assessment import Assessment
    from src.models.answer import Answer


class AttemptStatus(str, Enum):
    """Attempt status enumeration."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    SUBMITTED = "submitted"
    GRADED = "graded"
    EXPIRED = "expired"
    ABANDONED = "abandoned"


class AssessmentAttempt(Base, UUIDMixin, TimestampMixin):
    """AssessmentAttempt model representing a user's attempt at an assessment.
    
    Tracks the lifecycle of a user's interaction with an assessment,
    including timing, scoring, and navigation state.
    """
    
    __tablename__ = "assessment_attempts"
    
    # References
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Attempt tracking
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Status
    status: Mapped[AttemptStatus] = mapped_column(
        String(20),
        default=AttemptStatus.NOT_STARTED,
        nullable=False,
    )
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
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
    
    # Question navigation
    question_ids: Mapped[list[uuid.UUID]] = mapped_column(
        JSON,
        nullable=False,
    )
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    answered_questions: Mapped[list[uuid.UUID] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    flagged_questions: Mapped[list[uuid.UUID] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Scoring
    raw_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentage_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    scaled_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passing_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    
    # Points
    points_earned: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Answer tracking
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incorrect_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Feedback
    feedback_provided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanations_shown: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    review_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment",
        back_populates="attempts",
    )
    answers: Mapped[list["Answer"]] = relationship(
        "Answer",
        back_populates="attempt",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_attempts_user_assessment", "user_id", "assessment_id"),
        Index("ix_attempts_status", "status"),
        Index("ix_attempts_started", "started_at"),
        Index("ix_attempts_submitted", "submitted_at"),
    )
    
    def __repr__(self) -> str:
        return f"<AssessmentAttempt(id={self.id}, user={self.user_id}, status={self.status})>"
    
    @property
    def is_timed_out(self) -> bool:
        """Check if the attempt has exceeded its time limit."""
        if self.started_at and self.time_limit_minutes:
            now = datetime.now(timezone.utc)
            elapsed = (now - self.started_at).total_seconds()
            return elapsed > (self.time_limit_minutes * 60)
        return False
    
    @property
    def is_overdue(self) -> bool:
        """Check if the attempt is past its deadline."""
        if self.submitted_at:
            return False
        return self.is_timed_out
    
    @property
    def progress_percentage(self) -> float:
        """Calculate the progress percentage."""
        if not self.question_ids:
            return 0.0
        answered = len(self.answered_questions) if self.answered_questions else 0
        return (answered / len(self.question_ids)) * 100
    
    @property
    def is_complete(self) -> bool:
        """Check if the attempt is complete."""
        return self.status in (
            AttemptStatus.SUBMITTED,
            AttemptStatus.GRADED,
            AttemptStatus.EXPIRED,
        )
    
    @property
    def can_submit(self) -> bool:
        """Check if the attempt can be submitted."""
        return self.status == AttemptStatus.IN_PROGRESS and not self.is_overdue
    
    @property
    def remaining_time_seconds(self) -> int | None:
        """Calculate remaining time in seconds."""
        if not self.started_at or not self.time_limit_minutes:
            return None
        now = datetime.now(timezone.utc)
        elapsed = (now - self.started_at).total_seconds()
        remaining = (self.time_limit_minutes * 60) - elapsed
        return max(0, int(remaining))
