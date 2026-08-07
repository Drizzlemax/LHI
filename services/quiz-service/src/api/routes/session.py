"""
PANDORA Quiz Service Session API Routes
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.models import QuizSessionStatus
from src.schemas.session import (
    SessionCreate,
    SessionStart,
    SessionResponse,
    SessionSubmit,
    SessionListResponse,
)
from src.schemas.question import QuestionResponse
from src.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Create a new quiz session."""
    service = SessionService(db)
    session = await service.create_session(session_data)
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Get a session by ID."""
    service = SessionService(db)
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return SessionResponse.model_validate(session)


@router.post("/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionStart,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Start a quiz session."""
    service = SessionService(db)
    
    # Check for existing active session
    existing = await service.get_user_session(
        session_data.user_id,
        session_data.quiz_id,
        include_completed=False,
    )
    
    if existing:
        # Resume existing session
        if existing.status == QuizSessionStatus.PAUSED:
            session = await service.resume_session(existing.id)
        else:
            session = existing
    else:
        # Create and start new session
        session = await service.create_session(session_data)
        if session:
            session = await service.start_session(session.id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not start session",
        )
    
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/pause", response_model=SessionResponse)
async def pause_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Pause a quiz session."""
    service = SessionService(db)
    session = await service.pause_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not pause session",
        )
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/resume", response_model=SessionResponse)
async def resume_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Resume a paused session."""
    service = SessionService(db)
    session = await service.resume_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not resume session",
        )
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Complete a quiz session."""
    service = SessionService(db)
    session = await service.complete_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not complete session",
        )
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/abandon", response_model=SessionResponse)
async def abandon_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Abandon a quiz session."""
    service = SessionService(db)
    session = await service.abandon_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return SessionResponse.model_validate(session)


@router.get("/{session_id}/question", response_model=QuestionResponse | None)
async def get_current_question(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuestionResponse | None:
    """Get the current question in a session."""
    service = SessionService(db)
    question, _ = await service.get_current_question(session_id)
    if not question:
        return None
    return QuestionResponse.model_validate(question)


@router.get("/user/{user_id}", response_model=SessionListResponse)
async def list_user_sessions(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: QuizSessionStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> SessionListResponse:
    """List user's quiz sessions."""
    service = SessionService(db)
    sessions, total = await service.list_user_sessions(
        user_id=user_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    
    return SessionListResponse(
        items=[SessionResponse.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
    )
