"""
User and User-related models
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, SoftDeleteMixin


class UserRole(str, Enum):
    """User roles in the system."""

    ADMIN = "admin"
    INSTITUTION_ADMIN = "institution_admin"
    INSTRUCTOR = "instructor"
    LEARNER = "learner"
    GUEST = "guest"


class User(Base, SoftDeleteMixin):
    """User model representing authenticated users."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_role", "role"),
        {"schema": "public"},
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        String(50),
        default=UserRole.LEARNER,
        nullable=False,
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.institutions.id"),
        nullable=True,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    preferences: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    # Relationships
    institution: Mapped["Institution | None"] = relationship(
        "Institution",
        back_populates="users",
    )
    learning_profile: Mapped["LearningProfile | None"] = relationship(
        "LearningProfile",
        back_populates="user",
        uselist=False,
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Institution(Base):
    """Institution model for organizational accounts."""

    __tablename__ = "institutions"
    __table_args__ = (
        Index("ix_institutions_domain", "domain", unique=True),
        {"schema": "public"},
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    tier: Mapped[str] = mapped_column(
        String(50),
        default="free",
        nullable=False,
    )
    settings: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="institution",
    )


class LearningProfile(Base):
    """Learning profile storing user preferences and knowledge state."""

    __tablename__ = "learning_profiles"
    __table_args__ = (
        Index("ix_learning_profiles_user_id", "user_id", unique=True),
        {"schema": "public"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.id"),
        nullable=False,
        unique=True,
    )
    education_level: Mapped[str] = mapped_column(
        String(50),
        default="undergraduate",
        nullable=False,
    )
    target_education_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    knowledge_state: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    learning_style: Mapped[str] = mapped_column(
        String(50),
        default="mixed",
        nullable=False,
    )
    preferred_content_types: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )
    availability: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    accessibility_needs: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="learning_profile",
    )


class Session(Base):
    """Session model for JWT tracking and invalidation."""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_token_hash", "token_hash", unique=True),
        {"schema": "public"},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.id"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    refresh_token_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sessions",
    )
