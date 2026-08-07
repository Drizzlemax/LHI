"""
PANDORA Quiz Service Quiz Analytics Model
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin, UUIDMixin


class QuizAnalytics(Base, UUIDMixin, TimestampMixin):
    """Quiz analytics model for aggregated quiz statistics."""
    
    __tablename__ = "quiz_analytics"
    
    # Quiz reference
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Time period
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    # Attempt statistics
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    repeat_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Score statistics
    average_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    median_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    std_dev_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Pass/fail statistics
    pass_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fail_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Time statistics
    average_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Question analysis
    question_difficulty_actual: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    question_discrimination_actual: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Reliability metrics
    cronbach_alpha: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_error_measurement: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Item analysis
    item_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Example: {"question_id": {"p_value": 0.7, "rit": 0.45, "rir": 0.32}}
    
    # Indexes
    __table_args__ = (
        Index("ix_quiz_analytics_quiz_period", "quiz_id", "period_start", "period_end"),
    )
    
    def __repr__(self) -> str:
        return f"<QuizAnalytics(quiz={self.quiz_id}, avg={self.average_score:.1f})>"
