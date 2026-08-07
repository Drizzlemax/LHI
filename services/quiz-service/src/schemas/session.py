"""
PANDORA Quiz Service Session Schemas
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    """Schema for creating a quiz session."""
    quiz_id: uuid.UUID
    user_id: uuid.UUID


class SessionStart(BaseModel):
    """Schema for starting a quiz session."""
    quiz_id: uuid.UUID
    user_id: uuid.UUID


class CurrentQuestion(BaseModel):
    """Schema for current question in session."""
    id: uuid.UUID
    sequence_number: int
    stem: str
    question_type: str
    options: list[dict] | None = None
    points: float
    difficulty: float | None = None
    time_estimate_seconds: int | None = None


class SessionResponse(BaseModel):
    """Schema for session response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    quiz_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    question_ids: list[uuid.UUID]
    current_question_index: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    time_limit_minutes: int | None = None
    time_spent_seconds: int = 0
    last_activity_at: datetime | None = None
    raw_score: float = 0.0
    percentage_score: float | None = None
    scaled_score: float | None = None
    passed: bool | None = None
    estimated_ability: float = 0.0
    answered_questions: list[uuid.UUID] | None = None
    flagged_questions: list[uuid.UUID] | None = None
    current_question: CurrentQuestion | None = None
    progress_percentage: float = 0.0
    created_at: datetime


class SessionSubmit(BaseModel):
    """Schema for submitting a quiz session."""
    session_id: uuid.UUID
    feedback: str | None = None
    show_results: bool = True


class SessionListResponse(BaseModel):
    """Schema for session list response."""
    items: list[SessionResponse]
    total: int
    page: int
    page_size: int
