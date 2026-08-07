"""
PANDORA Quiz Service Question Model
"""
import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.quiz import Quiz
    from src.models.response import QuestionResponse


class QuestionDifficulty(str, Enum):
    """Question difficulty levels."""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class Question(Base, UUIDMixin, TimestampMixin):
    """Question model representing a quiz question."""
    
    __tablename__ = "questions"
    
    # Quiz reference
    quiz_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Content
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    
    # Options (for multiple choice, etc.)
    options: Mapped[list[dict] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    # Example: [{"id": "a", "text": "Option A", "is_correct": false}, ...]
    
    # Correct answer(s)
    correct_answer: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Example: {"type": "single", "value": "a"} or {"type": "multiple", "values": ["a", "c"]}
    
    # Difficulty and discrimination (IRT parameters)
    difficulty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    discrimination: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    guessing_parameter: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)
    
    # Metadata
    difficulty_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    
    # Bloom's taxonomy level
    cognitive_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    
    # Explanation
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Point value
    points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    # Statistics
    times_shown: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_correct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    times_incorrect: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Calculated statistics
    success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    item_total_correlation: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Active flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    quiz: Mapped["Quiz | None"] = relationship(
        "Quiz",
        back_populates="questions",
    )
    responses: Mapped[list["QuestionResponse"]] = relationship(
        "QuestionResponse",
        back_populates="question",
        lazy="selectin",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_questions_quiz", "quiz_id"),
        Index("ix_questions_difficulty", "difficulty"),
        Index("ix_questions_category", "category"),
    )
    
    def __repr__(self) -> str:
        return f"<Question(id={self.id}, type={self.question_type}, difficulty={self.difficulty})>"
    
    @property
    def success_rate_calc(self) -> float | None:
        """Calculate success rate."""
        if self.times_shown > 0:
            return self.times_correct / self.times_shown
        return None
