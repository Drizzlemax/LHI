"""
PANDORA Learning Service - Module Models
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
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
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.learning_path import LearningPath
    from src.models.path_lesson import PathLesson


class ModuleStatus(str, enum.Enum):
    """Module status enumeration."""
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class Module(Base):
    """
    Module model representing a section within a learning path.
    
    Modules are logical groupings of lessons that cover a specific topic
    or phase of the learning journey.
    """
    __tablename__ = "modules"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    learning_path_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Core fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Status
    status: Mapped[ModuleStatus] = mapped_column(
        SQLEnum(ModuleStatus, name="module_status"),
        default=ModuleStatus.LOCKED,
        nullable=False,
        index=True,
    )
    
    # Content metadata
    lesson_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Prerequisites - stored as JSON
    prerequisite_ids: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    
    # Progress
    progress_percentage: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    
    # Settings
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_bonus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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
    unlocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    learning_path: Mapped["LearningPath"] = relationship(
        "LearningPath",
        back_populates="modules",
    )
    lessons: Mapped[list["PathLesson"]] = relationship(
        "PathLesson",
        back_populates="module",
        order_by="PathLesson.order_index",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_modules_path_order", "learning_path_id", "order_index"),
        UniqueConstraint("learning_path_id", "order_index", name="uq_modules_path_order"),
    )
    
    def __repr__(self) -> str:
        return f"<Module(id={self.id}, title='{self.title}', order={self.order_index})>"
