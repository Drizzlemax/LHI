"""
PANDORA User Service User Routes
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routes.auth import get_current_user, get_db_session
from src.schemas.user import (
    UserProfileResponse,
    UserProfileUpdate,
    UserListResponse,
    PasswordChange,
    PasswordResetRequest,
    PasswordResetConfirm,
    LearningProfileResponse,
)
from src.schemas.auth import TokenPayload
from src.services.user_service import UserService, LearningProfileService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    token_payload: Annotated[TokenPayload, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    """Get the current authenticated user's profile."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(UUID(token_payload.sub))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, 'value') else user.role,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_verified=user.is_verified,
        mfa_enabled=user.mfa_enabled,
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    updates: UserProfileUpdate,
    token_payload: Annotated[TokenPayload, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    """Update the current user's profile."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(UUID(token_payload.sub))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if updates.full_name is not None:
        user.full_name = updates.full_name
    if updates.avatar_url is not None:
        user.avatar_url = updates.avatar_url
    if updates.preferences is not None:
        user.preferences = updates.preferences
    
    updated_user = await user_service.update_user(user)
    
    return UserProfileResponse(
        id=updated_user.id,
        email=updated_user.email,
        full_name=updated_user.full_name,
        role=updated_user.role.value if hasattr(updated_user.role, 'value') else updated_user.role,
        avatar_url=updated_user.avatar_url,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
        is_verified=updated_user.is_verified,
        mfa_enabled=updated_user.mfa_enabled,
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: UUID,
    token_payload: Annotated[TokenPayload, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    """Get a user's profile by ID."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, 'value') else user.role,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_verified=user.is_verified,
        mfa_enabled=user.mfa_enabled,
    )


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    role: str | None = None,
    token_payload: Annotated[TokenPayload, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db_session),
) -> UserListResponse:
    """List users with pagination (admin only)."""
    if token_payload.role not in ["admin", "institution_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    user_service = UserService(db)
    users = await user_service.list_users(skip=skip, limit=limit, role=role)
    total = await user_service.user_repo.count(role=role)
    
    user_profiles = [
        UserProfileResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value if hasattr(u.role, 'value') else u.role,
            avatar_url=u.avatar_url,
            created_at=u.created_at,
            updated_at=u.updated_at,
            is_verified=u.is_verified,
            mfa_enabled=u.mfa_enabled,
        )
        for u in users
    ]
    
    return UserListResponse(users=user_profiles, total=total, skip=skip, limit=limit)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: PasswordChange,
    token_payload: Annotated[TokenPayload, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Change the current user's password."""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(UUID(token_payload.sub))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    from src.core.security import verify_password
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    await user_service.change_password(user.id, request.new_password)
    
    if request.revoke_all_sessions:
        from src.services.user_service import AuthService
        auth_service = AuthService(db)
        await auth_service.logout_all(user.id)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    token_payload: Annotated[TokenPayload, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Soft delete the current user's account."""
    user_service = UserService(db)
    await user_service.delete_user(UUID(token_payload.sub))


@router.post("/verify-email/request")
async def request_email_verification(
    email: EmailStr,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Request email verification email."""
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    
    if not user or user.is_verified:
        return {"message": "If the email exists, a verification email has been sent"}
    
    return {"message": "If the email exists, a verification email has been sent"}


@router.post("/verify-email/confirm")
async def confirm_email_verification(
    token: str,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Confirm email verification with token."""
    from src.repositories.verification_repository import VerificationRepository
    
    verification_repo = VerificationRepository(db)
    user_service = UserService(db)
    
    verification = await verification_repo.get_valid_token(token)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    
    await user_service.verify_email(verification.user_id)
    await verification_repo.mark_used(token)
    
    return {"message": "Email verified successfully"}


@router.post("/reset-password/request")
async def request_password_reset(
    email: EmailStr,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Request password reset email."""
    return {"message": "If the email exists, a reset email has been sent"}


@router.post("/reset-password/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Confirm password reset with token."""
    from src.repositories.verification_repository import VerificationRepository
    
    verification_repo = VerificationRepository(db)
    user_service = UserService(db)
    
    verification = await verification_repo.get_valid_token(request.token)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    
    if verification.token_type != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type",
        )
    
    await user_service.change_password(verification.user_id, request.new_password)
    await verification_repo.mark_used(request.token)
    
    return {"message": "Password reset successfully"}


# Learning Profile Endpoints

@router.get("/me/learning-profile", response_model=LearningProfileResponse)
async def get_learning_profile(
    token_payload: Annotated[TokenPayload, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> LearningProfileResponse:
    """Get current user's learning profile."""
    profile_service = LearningProfileService(db)
    profile = await profile_service.get_profile(UUID(token_payload.sub))
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning profile not found",
        )
    
    return LearningProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        education_level=profile.education_level,
        target_education_level=profile.target_education_level,
        learning_style=profile.learning_style,
        preferred_content_types=profile.preferred_content_types or [],
        knowledge_state=profile.knowledge_state or {},
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.patch("/me/learning-profile", response_model=LearningProfileResponse)
async def update_learning_profile(
    education_level: str | None = None,
    target_education_level: str | None = None,
    learning_style: str | None = None,
    preferred_content_types: list[str] | None = None,
    token_payload: Annotated[TokenPayload, Depends(get_current_user)] = None,
    db: AsyncSession = Depends(get_db_session),
) -> LearningProfileResponse:
    """Update current user's learning profile."""
    profile_service = LearningProfileService(db)
    profile = await profile_service.update_profile(
        user_id=UUID(token_payload.sub),
        education_level=education_level,
        target_education_level=target_education_level,
        learning_style=learning_style,
        preferred_content_types=preferred_content_types,
    )
    
    return LearningProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        education_level=profile.education_level,
        target_education_level=profile.target_education_level,
        learning_style=profile.learning_style,
        preferred_content_types=profile.preferred_content_types or [],
        knowledge_state=profile.knowledge_state or {},
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
