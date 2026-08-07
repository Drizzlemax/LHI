"""
PANDORA Quiz Service Analytics Schemas
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QuizAnalyticsResponse(BaseModel):
    """Schema for quiz analytics response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    quiz_id: uuid.UUID
    period_start: datetime
    period_end: datetime
    total_attempts: int
    completed_attempts: int
    unique_users: int
    repeat_users: int
    average_score: float
    median_score: float | None = None
    std_dev_score: float | None = None
    min_score: float | None = None
    max_score: float | None = None
    pass_count: int
    fail_count: int
    pass_rate: float | None = None
    average_time_seconds: float | None = None
    median_time_seconds: float | None = None
    cronbach_alpha: float | None = None
    standard_error_measurement: float | None = None


class ItemAnalysisResponse(BaseModel):
    """Schema for item analysis response."""
    question_id: uuid.UUID
    difficulty_actual: float | None = None
    discrimination_actual: float | None = None
    p_value: float | None = None
    rit: float | None = None  # Point-biserial correlation
    rir: float | None = None  # Rest-of-item correlation
    times_shown: int
    times_correct: int
    success_rate: float | None = None
    updated_at: datetime


class ScoreDistribution(BaseModel):
    """Schema for score distribution."""
    range_0_20: int = 0
    range_20_40: int = 0
    range_40_60: int = 0
    range_60_80: int = 0
    range_80_100: int = 0


class TimeAnalysis(BaseModel):
    """Schema for time analysis."""
    average_time_seconds: float
    median_time_seconds: float | None = None
    min_time_seconds: float | None = None
    max_time_seconds: float | None = None
    total_time_hours: float


class PerformanceSummary(BaseModel):
    """Schema for performance summary."""
    total_attempts: int
    completed_attempts: int
    average_score: float
    median_score: float | None = None
    pass_rate: float
    average_time_minutes: float
    score_distribution: ScoreDistribution
    time_analysis: TimeAnalysis
