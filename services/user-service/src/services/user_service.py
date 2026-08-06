"""
User Service - Business logic for user operations
"""
from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from src.repositories.user_repository import (
    UserRepository,
    SessionRepository,
    LearningProfileRepository,
    InstitutionRepository,
)
from src.repositories.verification_repository import VerificationRepository
from src.models.user import User
from src.schemas.user import UserProfile, LearningProfile as LearningProfileSchema


class UserService:
    """Service for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.profile_repo = LearningProfileRepository(db)
        self.institution_repo = InstitutionRepository(db)
        self.verification_repo = VerificationRepository(db)

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "learner",
        institution_id: UUID | None = None,
    ) -> User:
        """Create a new user with hashed password."""
        password_hash = hash_password(password)
        user = await self.user_repo.create(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            institution_id=institution_id,
        )
        # Create learning profile automatically
        await self.profile_repo.create(user_id=user.id)
        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return await self.user_repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        return await self.user_repo.get_by_email(email)

    async def get_user_with_profile(self, user_id: UUID) -> User | None:
        """Get user with learning profile."""
        return await self.user_repo.get_with_profile(user_id)

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user with email and password."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def update_user(self, user: User, **kwargs) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(user, key) and key not in ["id", "password_hash"]:
                setattr(user, key, value)
        return await self.user_repo.update(user)

    async def change_password(self, user_id: UUID, new_password: str) -> bool:
        """Change user password."""
        password_hash = hash_password(new_password)
        return await self.user_repo.update_password(user_id, password_hash)

    async def verify_email(self, user_id: UUID) -> bool:
        """Verify user email."""
        return await self.user_repo.verify_email(user_id)

    async def delete_user(self, user_id: UUID) -> bool:
        """Soft delete a user."""
        return await self.user_repo.soft_delete(user_id)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: str | None = None,
    ) -> Sequence[User]:
        """List users with pagination."""
        return await self.user_repo.list_users(skip=skip, limit=limit, role=role)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.verification_repo = VerificationRepository(db)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "learner",
    ) -> tuple[User, str, str]:
        """
        Register a new user and return tokens.
        
        Returns:
            Tuple of (user, access_token, refresh_token)
        """
        user = await self.user_service.create_user(
            email=email,
            password=password,
            full_name=full_name,
            role=role,
        )
        
        # Generate tokens
        access_token = self._create_tokens_for_user(user.id, user.email, user.role)["access_token"]
        refresh_token = self._create_tokens_for_user(user.id, user.email, user.role)["refresh_token"]
        
        return user, access_token, refresh_token

    async def login(
        self,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, str, str] | None:
        """
        Login user and return tokens.
        
        Returns:
            Tuple of (user, access_token, refresh_token) or None if authentication fails
        """
        user = await self.user_service.authenticate_user(email, password)
        if not user:
            return None

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.user_repo.update(user)

        # Generate tokens
        access_token = self._create_tokens_for_user(user.id, user.email, user.role)["access_token"]
        refresh_token = self._create_tokens_for_user(user.id, user.email, user.role)["refresh_token"]
        
        # Create session
        await self.session_repo.create(
            user_id=user.id,
            token_hash=self._hash_token(access_token),
            refresh_token_hash=self._hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        
        return user, access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str] | None:
        """
        Refresh access token using refresh token.
        
        Returns:
            Tuple of (new_access_token, new_refresh_token) or None if invalid
        """
        token_hash = self._hash_token(refresh_token)
        session = await self.session_repo.get_by_token_hash(token_hash)
        
        if not session:
            return None

        user = await self.user_repo.get_by_id(session.user_id)
        if not user:
            return None

        # Generate new tokens
        new_access_token = self._create_tokens_for_user(user.id, user.email, user.role)["access_token"]
        new_refresh_token = self._create_tokens_for_user(user.id, user.email, user.role)["refresh_token"]
        
        # Update session
        session.token_hash = self._hash_token(new_access_token)
        session.refresh_token_hash = self._hash_token(new_refresh_token)
        session.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        return new_access_token, new_refresh_token

    async def logout(self, access_token: str) -> bool:
        """Logout user by revoking session."""
        token_hash = self._hash_token(access_token)
        return await self.session_repo.revoke_by_token_hash(token_hash)

    async def logout_all(self, user_id: UUID) -> int:
        """Logout user from all sessions."""
        return await self.session_repo.revoke_all_user_sessions(user_id)

    def _create_tokens_for_user(self, user_id: UUID, email: str, role: str) -> dict:
        """Create access and refresh tokens for user."""
        access_token = create_access_token({
            "sub": str(user_id),
            "email": email,
            "role": role,
        })
        refresh_token = create_refresh_token({
            "sub": str(user_id),
            "email": email,
            "role": role,
        })
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()


class LearningProfileService:
    """Service for learning profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = LearningProfileRepository(db)

    async def get_profile(self, user_id: UUID):
        """Get learning profile for user."""
        return await self.profile_repo.get_by_user_id(user_id)

    async def update_profile(
        self,
        user_id: UUID,
        education_level: str | None = None,
        target_education_level: str | None = None,
        learning_style: str | None = None,
        preferred_content_types: list[str] | None = None,
        knowledge_state: dict | None = None,
    ):
        """Update learning profile."""
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            # Create profile if it doesn't exist
            profile = await self.profile_repo.create(
                user_id=user_id,
                education_level=education_level or "undergraduate",
                learning_style=learning_style or "mixed",
            )
            return profile

        if education_level is not None:
            profile.education_level = education_level
        if target_education_level is not None:
            profile.target_education_level = target_education_level
        if learning_style is not None:
            profile.learning_style = learning_style
        if preferred_content_types is not None:
            profile.preferred_content_types = preferred_content_types
        if knowledge_state is not None:
            profile.knowledge_state = knowledge_state

        return await self.profile_repo.update(profile)

    async def update_knowledge_state(
        self, user_id: UUID, concept: str, level: int, mastery: float
    ) -> bool:
        """Update knowledge state for a concept."""
        return await self.profile_repo.update_knowledge_state(user_id, concept, level, mastery)
