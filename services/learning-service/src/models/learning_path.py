"""
PANDORA Learning Service - Learning Path Models
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.module import Module


class LearningPathStatus(str, enum.Enum):
    """Learning path status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class LearningPath(Base):
    """
    Learning Path model representing a structured learning journey.
    
    A learning path is a curated sequence of modules containing lessons
    that guide users through educational content.
    """
    __tablename__ = "learning_paths"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Core fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Status and progress
    status: Mapped[LearningPathStatus] = mapped_column(
        SQLEnum(LearningPathStatus, name="learning_path_status"),
        default=LearningPathStatus.DRAFT,
        nullable=False,
        index=True,
    )
    progress_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Settings
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_enrolled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_early_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Education level targeting
    target_education_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    difficulty_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Content metadata
    module_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lesson_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Analytics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enrollment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    modules: Mapped[list["Module"]] = relationship(
        "Module",
        back_populates="learning_path",
        order_by="Module.order_index",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    enrollments: Mapped["LearningPathEnrollment"] = relationship(
        "LearningPathEnrollment",
        back_populates="learning_path",
        cascade="all, delete-orphan",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_learning_paths_status_created", "status", "created_at"),
        Index("ix_learning_paths_user_status", "user_id", "status"),
        Index("ix_learning_paths_target_level_status", "target_education_level", "status"),
        UniqueConstraint("user_id", "course_id", name="uq_learning_paths_user_course"),
    )
    
    def __repr__(self) -> str:
        return f"<LearningPath(id={self.id}, title='{self.title}', status={self.status})>"
