"""
PANDORA Quiz Service Response API Routes
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.response import (
    ResponseSubmit,
    ResponseResponse,
    AnswerReview,
)
from src.schemas.question import QuestionWithAnswer
from src.services.response_service import ResponseService
from src.services.session_service import SessionService

router = APIRouter(prefix="/responses", tags=["responses"])


@router.post("/", response_model=ResponseResponse)
async def submit_response(
    response_data: ResponseSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResponseResponse:
    """Submit a response to a question."""
    session_service = SessionService(db)
    response_service = ResponseService(db)
    
    # Get session
    session = await session_service.get_session(response_data.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    
    # Get or create response
    response = await response_service.get_response(
        response_data.session_id,
        response_data.question_id,
    )
    
    if not response:
        # Create new response
        response = await response_service.create_response(
            session_id=response_data.session_id,
            question_id=response_data.question_id,
            sequence_number=session.current_question_index,
            ability_at_time=session.estimated_ability,
        )
    
    # Submit the answer
    response = await response_service.submit_response(
        session_id=response_data.session_id,
        question_id=response_data.question_id,
        user_answer=response_data.user_answer,
        time_spent_seconds=response_data.time_spent_seconds,
    )
    
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not submit response",
        )
    
    # Update session's answered questions
    answered = session.answered_questions or []
    if response_data.question_id not in answered:
        answered.append(response_data.question_id)
        session.answered_questions = answered
    
    # Move to next question
    session.current_question_index += 1
    
    await db.flush()
    
    return ResponseResponse.model_validate(response)


@router.post("/{session_id}/{question_id}/flag", response_model=ResponseResponse)
async def flag_question(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    is_flagged: bool = True,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResponseResponse:
    """Flag or unflag a question for review."""
    response_service = ResponseService(db)
    
    response = await response_service.update_flag(session_id, question_id, is_flagged)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found",
        )
    
    return ResponseResponse.model_validate(response)


@router.post("/{session_id}/{question_id}/skip", response_model=ResponseResponse)
async def skip_question(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResponseResponse:
    """Mark a question as skipped."""
    response_service = ResponseService(db)
    
    response = await response_service.mark_skipped(session_id, question_id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found",
        )
    
    return ResponseResponse.model_validate(response)


@router.get("/{session_id}/{question_id}/review", response_model=AnswerReview)
async def review_answer(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnswerReview:
    """Get answer review for a question."""
    response_service = ResponseService(db)
    
    response, question = await response_service.get_answer_for_review(
        session_id, question_id
    )
    
    if not response or not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response or question not found",
        )
    
    # Mark explanation as shown
    await response_service.show_explanation(session_id, question_id)
    
    return AnswerReview(
        question_id=question.id,
        stem=question.stem,
        question_type=question.question_type,
        options=question.options,
        user_answer=response.user_answer,
        correct_answer=question.correct_answer,
        is_correct=response.is_correct,
        partial_score=response.partial_score,
        explanation=question.explanation,
        time_spent_seconds=response.time_spent_seconds,
        points_earned=response.partial_score or 0.0,
    )


@router.get("/{session_id}", response_model=list[ResponseResponse])
async def get_session_responses(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ResponseResponse]:
    """Get all responses for a session."""
    response_service = ResponseService(db)
    responses = await response_service.get_session_responses(session_id)
    return [ResponseResponse.model_validate(r) for r in responses]
