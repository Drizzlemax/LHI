"""
PANDORA Learning Service Learning Paths Routes
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.database import get_db
from src.schemas.learning_path import (
    LearningPathCreate,
    LearningPathUpdate,
    LearningPathSummary,
    LearningPathDetail,
    LearningPathListResponse,
    LearningPathProgress,
    EnrollmentResponse,
)
from src.services.learning_path_service import LearningPathService
from src.models import LearningPathStatus

router = APIRouter()
logger = get_logger(__name__)


# ============ Routes ============

@router.get("/", response_model=LearningPathListResponse)
async def list_learning_paths(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    user_id: UUID | None = None,
    status: str | None = None,
    target_education_level: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> LearningPathListResponse:
    """
    List learning paths.
    
    Returns paginated list of learning paths, optionally filtered by user, status, or education level.
    """
    status_enum = LearningPathStatus(status) if status else None
    
    service = LearningPathService(db)
    paths, total = await service.list_learning_paths(
        skip=skip,
        limit=limit,
        user_id=user_id,
        status=status_enum,
        target_education_level=target_education_level,
    )
    
    return LearningPathListResponse(
        paths=[LearningPathSummary.model_validate(p) for p in paths],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=LearningPathDetail)
async def create_learning_path(
    data: LearningPathCreate,
    user_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> LearningPathDetail:
    """
    Create a new learning path.
    
    Creates a personalized learning path with optional modules.
    """
    service = LearningPathService(db)
    path = await service.create_learning_path(data, user_id)
    
    # Fetch with modules
    path = await service.get_learning_path(path.id, include_modules=True)
    return LearningPathDetail.model_validate(path)


@router.get("/{path_id}", response_model=LearningPathDetail)
async def get_learning_path(
    path_id: UUID,
    user_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> LearningPathDetail:
    """Get learning path by ID with full details."""
    service = LearningPathService(db)
    
    if user_id:
        path = await service.get_learning_path_by_user(path_id, user_id)
    else:
        path = await service.get_learning_path(path_id)
    
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found",
        )
    
    return LearningPathDetail.model_validate(path)


@router.patch("/{path_id}", response_model=LearningPathSummary)
async def update_learning_path(
    path_id: UUID,
    data: LearningPathUpdate,
    db: AsyncSession = Depends(get_db),
) -> LearningPathSummary:
    """Update a learning path."""
    service = LearningPathService(db)
    path = await service.update_learning_path(path_id, data)
    
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found",
        )
    
    return LearningPathSummary.model_validate(path)


@router.delete("/{path_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_learning_path(
    path_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (soft) a learning path."""
    service = LearningPathService(db)
    deleted = await service.delete_learning_path(path_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found",
        )


@router.post("/{path_id}/publish", response_model=LearningPathSummary)
async def publish_learning_path(
    path_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> LearningPathSummary:
    """Publish a learning path."""
    service = LearningPathService(db)
    path = await service.publish_learning_path(path_id)
    
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found",
        )
    
    return LearningPathSummary.model_validate(path)


@router.post("/{path_id}/enroll", response_model=EnrollmentResponse)
async def enroll_in_learning_path(
    path_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EnrollmentResponse:
    """Enroll user in a learning path."""
    service = LearningPathService(db)
    enrollment = await service.enroll_in_learning_path(path_id, user_id)
    return EnrollmentResponse.model_validate(enrollment)


@router.delete("/{path_id}/enroll", status_code=status.HTTP_204_NO_CONTENT)
async def unenroll_from_learning_path(
    path_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Unenroll user from a learning path."""
    service = LearningPathService(db)
    success = await service.unenroll_from_learning_path(path_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )


@router.get("/{path_id}/progress", response_model=LearningPathProgress)
async def get_learning_path_progress(
    path_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> LearningPathProgress:
    """Get user's progress in a learning path."""
    service = LearningPathService(db)
    progress = await service.get_path_progress(path_id, user_id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning path not found",
        )
    
    return progress
