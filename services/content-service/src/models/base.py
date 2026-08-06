"""
PANDORA Content Service Models Base
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=None,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=None,
        onupdate=None,
        nullable=False,
    )
    
    def on_create(self) -> None:
        """Set timestamps on creation."""
        now = datetime.now(timezone.utc)
        self.created_at = now
        self.updated_at = now
    
    def on_update(self) -> None:
        """Update timestamp on modification."""
        self.updated_at = datetime.now(timezone.utc)
