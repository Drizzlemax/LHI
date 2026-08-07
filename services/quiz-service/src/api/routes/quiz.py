"""
PANDORA Quiz Service Quiz API Routes
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import QuizStatus
from src.schemas.quiz import QuizCreate, QuizUpdate, QuizResponse, QuizListResponse
from src.services.quiz_service import QuizService

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.post("/", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    """Create a new quiz."""
    service = QuizService(db)
    quiz = await service.create_quiz(quiz_data)
    return QuizResponse.model_validate(quiz)


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    """Get a quiz by ID."""
    service = QuizService(db)
    quiz = await service.get_quiz(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )
    return QuizResponse.model_validate(quiz)


@router.patch("/{quiz_id}", response_model=QuizResponse)
async def update_quiz(
    quiz_id: uuid.UUID,
    quiz_data: QuizUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    """Update a quiz."""
    service = QuizService(db)
    quiz = await service.update_quiz(quiz_id, quiz_data)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )
    return QuizResponse.model_validate(quiz)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a quiz (soft delete)."""
    service = QuizService(db)
    deleted = await service.delete_quiz(quiz_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )


@router.post("/{quiz_id}/publish", response_model=QuizResponse)
async def publish_quiz(
    quiz_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    """Publish a quiz."""
    service = QuizService(db)
    quiz = await service.publish_quiz(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )
    return QuizResponse.model_validate(quiz)


@router.post("/{quiz_id}/archive", response_model=QuizResponse)
async def archive_quiz(
    quiz_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuizResponse:
    """Archive a quiz."""
    service = QuizService(db)
    quiz = await service.archive_quiz(quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )
    return QuizResponse.model_validate(quiz)


@router.get("/", response_model=QuizListResponse)
async def list_quizzes(
    db: Annotated[AsyncSession, Depends(get_db)],
    status: QuizStatus | None = None,
    learning_path_id: uuid.UUID | None = None,
    module_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> QuizListResponse:
    """List quizzes with filters."""
    service = QuizService(db)
    quizzes, total = await service.list_quizzes(
        status=status,
        learning_path_id=learning_path_id,
        module_id=module_id,
        page=page,
        page_size=page_size,
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return QuizListResponse(
        items=[QuizResponse.model_validate(q) for q in quizzes],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
