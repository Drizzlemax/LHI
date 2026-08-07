"""
PANDORA Quiz Service Assessment Question Model
"""
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.assessment import Assessment
    from src.models.answer import Answer


class AssessmentQuestionDifficulty(str, Enum):
    """Question difficulty levels for assessments."""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class AssessmentQuestionType(str, Enum):
    """Question types for assessments."""
    MULTIPLE_CHOICE = "multiple_choice"
    MULTIPLE_SELECT = "multiple_select"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    FILL_BLANK = "fill_blank"
    MATCHING = "matching"
    RANKING = "ranking"
    NUMERICAL = "numerical"
    FILE_UPLOAD = "file_upload"


class BloomLevel(str, Enum):
    """Bloom's taxonomy cognitive levels."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class AssessmentQuestion(Base, UUIDMixin, TimestampMixin):
    """AssessmentQuestion model representing a question within an assessment.
    
    Stores question content, metadata, and difficulty parameters
    for use in assessments.
    """
    
    __tablename__ = "assessment_questions"
    
    # Assessment reference
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Content
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)  # Alias for stem
    question_type: Mapped[AssessmentQuestionType] = mapped_column(
        String(30),
        default=AssessmentQuestionType.MULTIPLE_CHOICE,
        nullable=False,
    )
    
    # Options (for multiple choice, matching, etc.)
    options: Mapped[list[dict] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    # Example: [{"id": "a", "text": "Option A", "is_correct": false}, ...]
    
    # Correct answer(s)
    correct_answer: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Example: {"type": "single", "value": "a"} or {"type": "multiple", "values": ["a", "c"]}
    
    # Partial credit settings
    partial_credit_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    partial_credit_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Difficulty parameters
    difficulty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    difficulty_label: Mapped[AssessmentQuestionDifficulty | None] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # IRT parameters (for adaptive testing)
    discrimination: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    guessing_parameter: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    
    # Metadata
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    cognitive_level: Mapped[BloomLevel | None] = mapped_column(String(30), nullable=True)
    
    # Point value
    points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # Explanation (shown after answering)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Media
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Time estimate
    estimated_time_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Statistics (updated periodically)
    times_shown: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_correct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_incorrect: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Calculated statistics
    success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    item_difficulty_actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    discrimination_actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    assessment: Mapped["Assessment"] = relationship(
        "Assessment",
        back_populates="questions",
    )
    answers: Mapped[list["Answer"]] = relationship(
        "Answer",
        back_populates="question",
        lazy="selectin",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_assessment_questions_assessment", "assessment_id"),
        Index("ix_assessment_questions_difficulty", "difficulty"),
        Index("ix_assessment_questions_category", "category"),
        Index("ix_assessment_questions_type", "question_type"),
    )
    
    def __repr__(self) -> str:
        return f"<AssessmentQuestion(id={self.id}, type={self.question_type}, points={self.points})>"
    
    @property
    def success_rate_calc(self) -> float | None:
        """Calculate success rate from statistics."""
        if self.times_shown > 0:
            return self.times_correct / self.times_shown
        return None
    
    @property
    def average_time(self) -> float | None:
        """Get average time to answer."""
        return self.average_time_seconds
    
    def update_statistics(self) -> None:
        """Update calculated statistics."""
        if self.times_shown > 0:
            self.success_rate = self.times_correct / self.times_shown
