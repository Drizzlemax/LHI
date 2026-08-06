"""
PANDORA User Service User Schemas
Pydantic models for user management endpoints
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserProfileUpdate(BaseModel):
    """Request schema for updating user profile."""

    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)


class LearningProfileUpdate(BaseModel):
    """Request schema for updating learning profile."""

    education_level: str | None = Field(
        default=None,
        description="Current education level (elementary, middle_school, high_school, undergraduate, graduate, doctoral)"
    )
    target_education_level: str | None = Field(
        default=None,
        description="Target education level to achieve"
    )
    knowledge_state: dict | None = Field(
        default=None,
        description="Mastery levels for various concepts"
    )
    learning_style: str | None = Field(
        default=None,
        description="Preferred learning style (visual, auditory, reading, kinesthetic, mixed)"
    )
    preferred_content_types: list[str] | None = Field(
        default=None,
        description="Preferred content formats (video, text, interactive, etc.)"
    )


class UserPreferencesUpdate(BaseModel):
    """Request schema for updating user preferences."""

    language: str | None = Field(default="en", max_length=10)
    theme: str | None = Field(
        default="system",
        description="UI theme (light, dark, system)"
    )
    notifications: dict | None = Field(
        default=None,
        description="Notification settings"
    )
    display: dict | None = Field(
        default=None,
        description="Display settings"
    )


class InstitutionSummary(BaseModel):
    """Summary schema for institution."""

    id: UUID
    name: str
    domain: str


class UserProfile(BaseModel):
    """Response schema for user profile."""

    id: UUID
    email: str
    full_name: str
    role: str
    avatar_url: str | None = None
    institution: InstitutionSummary | None = None
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    mfa_enabled: bool


class LearningProfile(BaseModel):
    """Response schema for learning profile."""

    id: UUID
    user_id: UUID
    education_level: str
    target_education_level: str | None = None
    knowledge_state: dict
    learning_style: str
    preferred_content_types: list[str] | None = None
    availability: dict | None = None
    accessibility_needs: dict | None = None
    updated_at: datetime


class UserPreferences(BaseModel):
    """Response schema for user preferences."""

    language: str = "en"
    theme: str = "system"
    notifications: dict = Field(default_factory=dict)
    display: dict = Field(default_factory=dict)
