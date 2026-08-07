"""
PANDORA Quiz Service Response Schemas
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResponseCreate(BaseModel):
    """Schema for creating a response."""
    session_id: uuid.UUID
    question_id: uuid.UUID
    user_answer: dict | None = None


class ResponseUpdate(BaseModel):
    """Schema for updating a response."""
    user_answer: dict | None = None
    is_flagged: bool | None = None
    is_skipped: bool | None = None


class ResponseSubmit(BaseModel):
    """Schema for submitting a response."""
    session_id: uuid.UUID
    question_id: uuid.UUID
    user_answer: dict = Field(..., description="The user's answer")
    time_spent_seconds: int = Field(default=0, ge=0)
    question_started_at: datetime | None = None


class ResponseResponse(BaseModel):
    """Schema for response response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    session_id: uuid.UUID
    question_id: uuid.UUID
    user_answer: dict | None = None
    is_correct: bool | None = None
    partial_score: float | None = None
    time_spent_seconds: int = 0
    sequence_number: int
    ability_at_time: float | None = None
    difficulty_at_time: float | None = None
    is_flagged: bool = False
    is_skipped: bool = False
    was_changed: bool = False
    explanation: str | None = None
    created_at: datetime


class AnswerReview(BaseModel):
    """Schema for answer review."""
    question_id: uuid.UUID
    stem: str
    question_type: str
    options: list[dict] | None = None
    user_answer: dict | None = None
    correct_answer: dict | None = None
    is_correct: bool | None = None
    partial_score: float | None = None
    explanation: str | None = None
    time_spent_seconds: int = 0
    points_earned: float = 0.0
