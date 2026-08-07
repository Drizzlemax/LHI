"""
PANDORA Learning Service Progress Routes
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.database import get_db
from src.schemas.learning_path import ProgressUpdate
from src.services.learning_path_service import LearningPathService

router = APIRouter()
logger = get_logger(__name__)


# ============ Routes ============

@router.patch("/{path_id}/lessons/{lesson_id}/progress")
async def update_lesson_progress(
    path_id: UUID,
    lesson_id: UUID,
    user_id: UUID,
    data: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update progress for a lesson in a learning path.
    
    Updates lesson progress including status, time spent, and quiz results.
    """
    service = LearningPathService(db)
    progress = await service.update_lesson_progress(path_id, lesson_id, user_id, data)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress record not found",
        )
    
    return {
        "id": str(progress.id),
        "lesson_id": str(progress.lesson_id),
        "status": progress.status.value,
        "progress_percentage": progress.progress_percentage,
        "score": progress.score,
        "time_spent_seconds": progress.time_spent_seconds,
    }


@router.post("/{path_id}/lessons/{lesson_id}/complete")
async def complete_lesson(
    path_id: UUID,
    lesson_id: UUID,
    user_id: UUID,
    score: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a lesson as completed.
    
    Finalizes lesson progress with optional score.
    """
    service = LearningPathService(db)
    
    data = ProgressUpdate(
        status="completed",
        progress_percentage=100.0,
        score=score,
    )
    
    progress = await service.update_lesson_progress(path_id, lesson_id, user_id, data)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress record not found",
        )
    
    return {
        "id": str(progress.id),
        "lesson_id": str(progress.lesson_id),
        "status": progress.status.value,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
    }


@router.post("/{path_id}/lessons/{lesson_id}/start")
async def start_lesson(
    path_id: UUID,
    lesson_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a lesson as in progress.
    
    Records the start of lesson consumption.
    """
    service = LearningPathService(db)
    
    data = ProgressUpdate(
        status="in_progress",
    )
    
    progress = await service.update_lesson_progress(path_id, lesson_id, user_id, data)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Progress record not found",
        )
    
    return {
        "id": str(progress.id),
        "lesson_id": str(progress.lesson_id),
        "status": progress.status.value,
        "started_at": progress.started_at.isoformat() if progress.started_at else None,
    }
