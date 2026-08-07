"""
PANDORA Learning Service - Learning Path Schemas
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============ Module Schemas ============

class ModuleBase(BaseModel):
    """Base module schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    order_index: int = Field(..., ge=0)
    estimated_hours: float | None = None
    is_optional: bool = False
    is_bonus: bool = False


class ModuleCreate(ModuleBase):
    """Schema for creating a module."""
    pass


class ModuleUpdate(BaseModel):
    """Schema for updating a module."""
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    order_index: int | None = Field(None, ge=0)
    estimated_hours: float | None = None
    is_optional: bool | None = None
    is_bonus: bool | None = None


class PathLessonSummary(BaseModel):
    """Summary of a lesson within a module."""
    id: uuid.UUID
    title: str
    lesson_type: str
    order_index: int
    estimated_minutes: int | None = None
    points: int = 0
    xp_reward: int = 0
    status: str = "locked"
    is_optional: bool = False
    is_preview: bool = False

    model_config = {"from_attributes": True}


class ModuleSummary(BaseModel):
    """Summary module schema for list views."""
    id: uuid.UUID
    title: str
    description: str | None = None
    order_index: int
    status: str
    lesson_count: int = 0
    progress_percentage: float = 0.0
    estimated_hours: float | None = None
    is_optional: bool = False
    is_bonus: bool = False

    model_config = {"from_attributes": True}


class ModuleDetail(ModuleSummary):
    """Detailed module schema with lessons."""
    lessons: list[PathLessonSummary] = []
    created_at: datetime
    updated_at: datetime
    unlocked_at: datetime | None = None
    completed_at: datetime | None = None


# ============ Lesson Schemas ============

class LessonBase(BaseModel):
    """Base lesson schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    lesson_type: Literal[
        "video", "article", "quiz", "assignment", "project",
        "live_session", "interactive", "exam"
    ] = "article"
    order_index: int = Field(..., ge=0)
    estimated_minutes: int | None = None
    points: int = 0
    xp_reward: int = 0
    is_optional: bool = False
    is_preview: bool = False
    is_bonus: bool = False
    content_config: dict | None = None
    completion_requirements: dict | None = None


class LessonCreate(LessonBase):
    """Schema for creating a lesson."""
    content_id: uuid.UUID | None = None


class LessonUpdate(BaseModel):
    """Schema for updating a lesson."""
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    lesson_type: str | None = None
    order_index: int | None = Field(None, ge=0)
    estimated_minutes: int | None = None
    points: int | None = None
    xp_reward: int | None = None
    is_optional: bool | None = None
    is_preview: bool | None = None
    is_bonus: bool | None = None
    content_config: dict | None = None
    completion_requirements: dict | None = None


class LessonDetail(LessonBase):
    """Detailed lesson schema."""
    id: uuid.UUID
    module_id: uuid.UUID
    content_id: uuid.UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    unlocked_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


# ============ Learning Path Schemas ============

class LearningPathBase(BaseModel):
    """Base learning path schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    goal: str | None = None
    target_education_level: str | None = None
    difficulty_level: str | None = None
    is_public: bool = False


class LearningPathCreate(LearningPathBase):
    """Schema for creating a learning path."""
    modules: list[ModuleCreate] = []


class LearningPathUpdate(BaseModel):
    """Schema for updating a learning path."""
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    goal: str | None = None
    target_education_level: str | None = None
    difficulty_level: str | None = None
    is_public: bool | None = None


class LearningPathSummary(BaseModel):
    """Summary learning path schema for list views."""
    id: uuid.UUID
    title: str
    description: str | None = None
    status: str
    progress_percentage: float = 0.0
    module_count: int = 0
    lesson_count: int = 0
    estimated_hours: int | None = None
    target_education_level: str | None = None
    difficulty_level: str | None = None
    is_public: bool = False
    is_featured: bool = False
    enrollment_count: int = 0
    rating: float | None = None
    rating_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LearningPathDetail(LearningPathSummary):
    """Detailed learning path schema with modules."""
    modules: list[ModuleDetail] = []
    published_at: datetime | None = None


class LearningPathListResponse(BaseModel):
    """Response for listing learning paths."""
    paths: list[LearningPathSummary]
    total: int
    skip: int
    limit: int


# ============ Progress Schemas ============

class ProgressUpdate(BaseModel):
    """Schema for updating lesson progress."""
    status: Literal[
        "not_started", "in_progress", "completed", "failed", "skipped"
    ] | None = None
    progress_percentage: float | None = Field(None, ge=0, le=100)
    time_spent_seconds: int | None = Field(None, ge=0)
    last_position_seconds: int | None = Field(None, ge=0)
    score: float | None = Field(None, ge=0, le=100)
    quiz_results: dict | None = None


class LessonProgress(BaseModel):
    """Progress for a single lesson."""
    lesson_id: uuid.UUID
    title: str
    lesson_type: str
    status: str
    progress_percentage: float = 0.0
    score: float | None = None
    time_spent_seconds: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ModuleProgress(BaseModel):
    """Progress for a single module."""
    module_id: uuid.UUID
    title: str
    status: str
    progress_percentage: float = 0.0
    lessons: list[LessonProgress] = []
    completed_lessons: int = 0
    total_lessons: int = 0


class LearningPathProgress(BaseModel):
    """Overall progress for a learning path."""
    learning_path_id: uuid.UUID
    title: str
    status: str
    progress_percentage: float = 0.0
    modules: list[ModuleProgress] = []
    completed_modules: int = 0
    total_modules: int = 0
    completed_lessons: int = 0
    total_lessons: int = 0
    total_time_spent_seconds: int = 0
    started_at: datetime | None = None
    last_activity_at: datetime | None = None


class EnrollmentResponse(BaseModel):
    """Response for enrollment."""
    id: uuid.UUID
    user_id: uuid.UUID
    learning_path_id: uuid.UUID
    progress_percentage: float
    enrolled_at: datetime
    started_at: datetime | None = None

    model_config = {"from_attributes": True}
