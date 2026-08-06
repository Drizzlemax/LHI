"""
User Repository - Database access layer for user operations
"""
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User, Session, LearningProfile, Institution
from src.models.base import SoftDeleteMixin


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        email: str,
        password_hash: str,
        full_name: str,
        role: str = "learner",
        institution_id: UUID | None = None,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            institution_id=institution_id,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID, include_deleted: bool = False) -> User | None:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        if not include_deleted:
            query = query.where(or_(User.is_deleted == False, User.is_deleted.is_(None)))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, include_deleted: bool = False) -> User | None:
        """Get user by email."""
        query = select(User).where(User.email == email)
        if not include_deleted:
            query = query.where(or_(User.is_deleted == False, User.is_deleted.is_(None)))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_profile(self, user_id: UUID) -> User | None:
        """Get user with learning profile loaded."""
        query = (
            select(User)
            .options(selectinload(User.learning_profile))
            .options(selectinload(User.institution))
            .where(User.id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_email_verification(self, email: str) -> User | None:
        """Get user by email with email verified check."""
        query = select(User).where(
            and_(
                User.email == email,
                or_(User.is_deleted == False, User.is_deleted.is_(None)),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """Update a user."""
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_password(self, user_id: UUID, password_hash: str) -> bool:
        """Update user password."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                password_hash=password_hash,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def verify_email(self, user_id: UUID) -> bool:
        """Mark user email as verified."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                is_verified=True,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def soft_delete(self, user_id: UUID) -> bool:
        """Soft delete a user."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                is_deleted=True,
                deleted_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: str | None = None,
    ) -> Sequence[User]:
        """List users with pagination."""
        query = select(User).where(or_(User.is_deleted == False, User.is_deleted.is_(None)))
        if role:
            query = query.where(User.role == role)
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count(self, role: str | None = None) -> int:
        """Count total users."""
        from sqlalchemy import func, select

        query = select(func.count(User.id)).where(
            or_(User.is_deleted == False, User.is_deleted.is_(None))
        )
        if role:
            query = query.where(User.role == role)
        result = await self.db.execute(query)
        return result.scalar_one()


class SessionRepository:
    """Repository for session management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        refresh_token_hash: str | None,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> Session:
        """Create a new session."""
        session = Session(
            user_id=user_id,
            token_hash=token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        """Get session by token hash."""
        query = select(Session).where(
            and_(
                Session.token_hash == token_hash,
                Session.is_revoked == False,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_sessions(self, user_id: UUID) -> Sequence[Session]:
        """Get all active sessions for a user."""
        query = (
            select(Session)
            .where(
                and_(
                    Session.user_id == user_id,
                    Session.is_revoked == False,
                )
            )
            .order_by(Session.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def revoke(self, session_id: UUID) -> bool:
        """Revoke a session."""
        stmt = update(Session).where(Session.id == session_id).values(is_revoked=True)
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def revoke_by_token_hash(self, token_hash: str) -> bool:
        """Revoke session by token hash."""
        stmt = update(Session).where(Session.token_hash == token_hash).values(is_revoked=True)
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def revoke_all_user_sessions(self, user_id: UUID) -> int:
        """Revoke all sessions for a user."""
        stmt = update(Session).where(Session.user_id == user_id).values(is_revoked=True)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def cleanup_expired(self) -> int:
        """Clean up expired sessions."""
        stmt = delete(Session).where(Session.expires_at < datetime.now(timezone.utc))
        result = await self.db.execute(stmt)
        return result.rowcount


class LearningProfileRepository:
    """Repository for learning profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        education_level: str = "undergraduate",
        learning_style: str = "mixed",
    ) -> LearningProfile:
        """Create a new learning profile."""
        profile = LearningProfile(
            user_id=user_id,
            education_level=education_level,
            learning_style=learning_style,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def get_by_user_id(self, user_id: UUID) -> LearningProfile | None:
        """Get learning profile by user ID."""
        query = select(LearningProfile).where(LearningProfile.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(self, profile: LearningProfile) -> LearningProfile:
        """Update a learning profile."""
        profile.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update_knowledge_state(
        self, user_id: UUID, concept: str, level: int, mastery: float
    ) -> bool:
        """Update knowledge state for a specific concept."""
        profile = await self.get_by_user_id(user_id)
        if not profile:
            return False

        knowledge_state = profile.knowledge_state or {}
        knowledge_state[concept] = {"level": level, "mastery": mastery}
        profile.knowledge_state = knowledge_state
        await self.db.flush()
        return True


class InstitutionRepository:
    """Repository for institution operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        name: str,
        domain: str,
        tier: str = "free",
    ) -> Institution:
        """Create a new institution."""
        institution = Institution(
            name=name,
            domain=domain,
            tier=tier,
        )
        self.db.add(institution)
        await self.db.flush()
        await self.db.refresh(institution)
        return institution

    async def get_by_id(self, institution_id: UUID) -> Institution | None:
        """Get institution by ID."""
        query = select(Institution).where(Institution.id == institution_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Institution | None:
        """Get institution by domain."""
        query = select(Institution).where(Institution.domain == domain)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
