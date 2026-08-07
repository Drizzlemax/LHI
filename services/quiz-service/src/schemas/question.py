"""
PANDORA Quiz Service Question Schemas
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuestionOption(BaseModel):
    """Schema for question option."""
    id: str
    text: str
    is_correct: bool = False


class QuestionCreate(BaseModel):
    """Schema for creating a question."""
    quiz_id: uuid.UUID | None = None
    stem: str = Field(..., min_length=1)
    question_type: str = Field(..., pattern="^(multiple_choice|multiple_select|true_false|short_answer|essay|fill_blank|matching|ranking)$")
    options: list[QuestionOption] | None = None
    correct_answer: dict | None = None
    difficulty: float = Field(default=0.0, ge=-4.0, le=4.0)
    discrimination: float = Field(default=1.0, ge=0.0, le=3.0)
    guessing_parameter: float = Field(default=0.25, ge=0.0, le=1.0)
    difficulty_label: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    cognitive_level: str | None = None
    explanation: str | None = None
    points: float = Field(default=1.0, ge=0)


class QuestionUpdate(BaseModel):
    """Schema for updating a question."""
    stem: str | None = Field(None, min_length=1)
    question_type: str | None = None
    options: list[QuestionOption] | None = None
    correct_answer: dict | None = None
    difficulty: float | None = Field(None, ge=-4.0, le=4.0)
    discrimination: float | None = Field(None, ge=0.0, le=3.0)
    guessing_parameter: float | None = Field(None, ge=0.0, le=1.0)
    difficulty_label: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    cognitive_level: str | None = None
    explanation: str | None = None
    points: float | None = Field(None, ge=0)
    is_active: bool | None = None
    is_approved: bool | None = None


class QuestionResponse(BaseModel):
    """Schema for question response (without correct answer)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    quiz_id: uuid.UUID | None = None
    stem: str
    question_type: str
    options: list[dict] | None = None
    difficulty: float
    discrimination: float
    difficulty_label: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    cognitive_level: str | None = None
    points: float
    times_shown: int = 0
    success_rate: float | None = None
    created_at: datetime


class QuestionWithAnswer(QuestionResponse):
    """Schema for question with correct answer (for review)."""
    correct_answer: dict | None = None
    explanation: str | None = None
