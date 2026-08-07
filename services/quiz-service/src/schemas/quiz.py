"""
PANDORA Quiz Service Quiz Schemas
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QuizBase(BaseModel):
    """Base quiz schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    question_type: Literal[
        "multiple_choice",
        "multiple_select",
        "true_false",
        "short_answer",
        "essay",
        "fill_blank",
        "matching",
        "ranking",
    ] = "multiple_choice"
    time_limit_minutes: int | None = Field(None, ge=1, le=480)
    allowed_attempts: int = Field(default=3, ge=1, le=100)
    cooldown_minutes: int | None = Field(None, ge=0)
    passing_score: float = Field(default=70.0, ge=0, le=100)
    max_score: float = Field(default=100.0, ge=0)
    points_per_question: float = Field(default=1.0, ge=0)
    is_adaptive: bool = False
    shuffle_questions: bool = False
    shuffle_answers: bool = False
    show_correct_answers: bool = True
    show_explanations: bool = True
    allow_back_navigation: bool = True
    learning_path_id: uuid.UUID | None = None
    module_id: uuid.UUID | None = None
    difficulty_level: str | None = None


class QuizCreate(QuizBase):
    """Schema for creating a quiz."""
    question_ids: list[uuid.UUID] | None = None


class QuizUpdate(BaseModel):
    """Schema for updating a quiz."""
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    question_ids: list[uuid.UUID] | None = None
    status: Literal["draft", "published", "archived", "deleted"] | None = None
    question_type: Literal[
        "multiple_choice",
        "multiple_select",
        "true_false",
        "short_answer",
        "essay",
        "fill_blank",
        "matching",
        "ranking",
    ] | None = None
    time_limit_minutes: int | None = Field(None, ge=1, le=480)
    allowed_attempts: int | None = Field(None, ge=1, le=100)
    cooldown_minutes: int | None = Field(None, ge=0)
    passing_score: float | None = Field(None, ge=0, le=100)
    max_score: float | None = Field(None, ge=0)
    points_per_question: float | None = Field(None, ge=0)
    is_adaptive: bool | None = None
    shuffle_questions: bool | None = None
    shuffle_answers: bool | None = None
    show_correct_answers: bool | None = None
    show_explanations: bool | None = None
    allow_back_navigation: bool | None = None


class QuizResponse(BaseModel):
    """Schema for quiz response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    question_type: str
    time_limit_minutes: int | None = None
    allowed_attempts: int
    passing_score: float
    max_score: float
    is_adaptive: bool
    shuffle_questions: bool
    shuffle_answers: bool
    show_correct_answers: bool
    show_explanations: bool
    allow_back_navigation: bool
    learning_path_id: uuid.UUID | None = None
    module_id: uuid.UUID | None = None
    difficulty_level: str | None = None
    total_attempts: int = 0
    average_score: float | None = None
    completion_rate: float | None = None
    created_at: datetime
    updated_at: datetime


class QuizListResponse(BaseModel):
    """Schema for quiz list response."""
    items: list[QuizResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
