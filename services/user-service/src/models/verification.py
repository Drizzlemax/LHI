"""
Verification Token model for email verification and password reset
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class VerificationToken(Base):
    """Token for email verification and password reset."""

    __tablename__ = "verification_tokens"
    __table_args__ = (
        Index("ix_verification_tokens_token", "token", unique=True),
        Index("ix_verification_tokens_user_id", "user_id"),
        {"schema": "public"},
    )

    class TokenType:
        EMAIL_VERIFICATION = "email_verification"
        PASSWORD_RESET = "password_reset"
        MFA_SETUP = "mfa_setup"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.users.id"),
        nullable=False,
    )
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    token_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_used: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="verification_tokens",
    )

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=None)

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_used and not self.is_expired


# Add back reference to User model
from src.models.user import User

if "verification_tokens" not in User.__dict__:
    User.verification_tokens = relationship(
        "VerificationToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
