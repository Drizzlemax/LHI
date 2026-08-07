"""
PANDORA Quiz Service Assessment Model
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.attempt import AssessmentAttempt
    from src.models.question import AssessmentQuestion


class AssessmentStatus(str, Enum):
    """Assessment status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class AssessmentType(str, Enum):
    """Assessment type enumeration."""
    QUIZ = "quiz"
    EXAM = "exam"
    HOMEWORK = "homework"
    PRACTICE = "practice"
    PLACEMENT = "placement"


class GradingType(str, Enum):
    """Grading type enumeration."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    HYBRID = "hybrid"


class Assessment(Base, UUIDMixin, TimestampMixin):
    """Assessment model representing an assessment or exam.
    
    An assessment is a collection of questions used to evaluate learner knowledge.
    It can be a quiz, exam, homework assignment, or practice test.
    """
    
    __tablename__ = "assessments"
    
    # Basic info
    content_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Type and status
    assessment_type: Mapped[AssessmentType] = mapped_column(
        String(20),
        default=AssessmentType.QUIZ,
        nullable=False,
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        String(20),
        default=AssessmentStatus.DRAFT,
        nullable=False,
    )
    
    # Timing
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allowed_attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cooldown_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Scoring
    passing_score: Mapped[float] = mapped_column(Float, default=60.0, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    grading_type: Mapped[GradingType] = mapped_column(
        String(20),
        default=GradingType.AUTOMATIC,
        nullable=False,
    )
    
    # Display options
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_explanations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_score_immediately: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Navigation options
    shuffle_questions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shuffle_answers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_back_navigation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_skip: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Availability
    available_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    available_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
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
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    
    # Statistics (updated via triggers or background jobs)
    question_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Relationships
    questions: Mapped[list["AssessmentQuestion"]] = relationship(
        "AssessmentQuestion",
        back_populates="assessment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    attempts: Mapped[list["AssessmentAttempt"]] = relationship(
        "AssessmentAttempt",
        back_populates="assessment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_assessments_status_created", "status", "created_at"),
        Index("ix_assessments_content", "content_id"),
        Index("ix_assessments_path_module", "learning_path_id", "module_id"),
        Index("ix_assessments_available", "available_from", "available_until"),
    )
    
    def __repr__(self) -> str:
        return f"<Assessment(id={self.id}, title='{self.title}', status={self.status})>"
    
    @property
    def is_available(self) -> bool:
        """Check if the assessment is currently available."""
        now = datetime.now(timezone.utc)
        if self.available_from and now < self.available_from:
            return False
        if self.available_until and now > self.available_until:
            return False
        return self.status == AssessmentStatus.PUBLISHED
    
    @property
    def is_open(self) -> bool:
        """Check if the assessment can be started."""
        return self.is_available and self.question_count > 0
