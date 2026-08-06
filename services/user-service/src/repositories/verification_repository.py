"""
Verification Repository - Database access for verification tokens
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.verification import VerificationToken


class VerificationRepository:
    """Repository for verification token operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        token: str,
        token_type: str,
        expires_in_hours: int = 24,
    ) -> VerificationToken:
        """Create a new verification token."""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        verification = VerificationToken(
            user_id=user_id,
            token=token,
            token_type=token_type,
            expires_at=expires_at,
        )
        self.db.add(verification)
        await self.db.flush()
        await self.db.refresh(verification)
        return verification

    async def get_by_token(self, token: str) -> VerificationToken | None:
        """Get verification token by token string."""
        query = select(VerificationToken).where(
            and_(
                VerificationToken.token == token,
                VerificationToken.is_used == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_valid_token(self, token: str) -> VerificationToken | None:
        """Get a valid (not expired, not used) verification token."""
        verification = await self.get_by_token(token)
        if verification and verification.is_valid:
            return verification
        return None

    async def mark_used(self, token: str) -> bool:
        """Mark a verification token as used."""
        stmt = (
            update(VerificationToken)
            .where(VerificationToken.token == token)
            .values(
                is_used=True,
                used_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def mark_used_by_id(self, token_id: UUID) -> bool:
        """Mark a verification token as used by ID."""
        stmt = (
            update(VerificationToken)
            .where(VerificationToken.id == token_id)
            .values(
                is_used=True,
                used_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def get_user_valid_tokens(
        self, user_id: UUID, token_type: str
    ) -> list[VerificationToken]:
        """Get all valid tokens for a user of a specific type."""
        query = select(VerificationToken).where(
            and_(
                VerificationToken.user_id == user_id,
                VerificationToken.token_type == token_type,
                VerificationToken.is_used == False,
                VerificationToken.expires_at > datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def invalidate_user_tokens(self, user_id: UUID, token_type: str | None = None) -> int:
        """Invalidate all tokens for a user."""
        conditions = [VerificationToken.user_id == user_id]
        if token_type:
            conditions.append(VerificationToken.token_type == token_type)

        stmt = delete(VerificationToken).where(and_(*conditions))
        result = await self.db.execute(stmt)
        return result.rowcount

    async def cleanup_expired(self) -> int:
        """Clean up expired tokens."""
        stmt = delete(VerificationToken).where(
            VerificationToken.expires_at < datetime.now(timezone.utc)
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def generate_email_verification_token(self, user_id: UUID) -> str:
        """Generate and store an email verification token."""
        import secrets
        token = secrets.token_urlsafe(32)
        await self.create(
            user_id=user_id,
            token=token,
            token_type=VerificationToken.TokenType.EMAIL_VERIFICATION,
            expires_in_hours=48,
        )
        return token

    async def generate_password_reset_token(self, user_id: UUID) -> str:
        """Generate and store a password reset token."""
        import secrets
        token = secrets.token_urlsafe(32)
        await self.create(
            user_id=user_id,
            token=token,
            token_type=VerificationToken.TokenType.PASSWORD_RESET,
            expires_in_hours=1,
        )
        return token
