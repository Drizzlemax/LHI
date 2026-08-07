"""
PANDORA Quiz Service Analytics API Routes
"""
import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.analytics import QuizAnalyticsResponse, PerformanceSummary
from src.services.analytics_service import QuizAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/quiz/{quiz_id}", response_model=QuizAnalyticsResponse)
async def get_quiz_analytics(
    quiz_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    period_days: int = Query(30, ge=1, le=365),
) -> QuizAnalyticsResponse:
    """Get analytics for a quiz."""
    service = QuizAnalyticsService(db)
    
    # Get or calculate analytics
    analytics = await service.get_quiz_analytics(quiz_id)
    
    if not analytics:
        # Calculate new analytics
        analytics = await service.calculate_and_save_analytics(
            quiz_id,
            period_days=period_days,
        )
    
    return QuizAnalyticsResponse.model_validate(analytics)


@router.get("/quiz/{quiz_id}/recalculate", response_model=QuizAnalyticsResponse)
async def recalculate_quiz_analytics(
    quiz_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    period_days: int = Query(30, ge=1, le=365),
) -> QuizAnalyticsResponse:
    """Recalculate analytics for a quiz."""
    service = QuizAnalyticsService(db)
    analytics = await service.calculate_and_save_analytics(
        quiz_id,
        period_days=period_days,
    )
    return QuizAnalyticsResponse.model_validate(analytics)


@router.get("/quiz/{quiz_id}/performance", response_model=PerformanceSummary)
async def get_quiz_performance(
    quiz_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: uuid.UUID | None = None,
) -> PerformanceSummary:
    """Get performance summary for a quiz."""
    service = QuizAnalyticsService(db)
    return await service.get_performance_summary(quiz_id, user_id)


@router.get("/quiz/{quiz_id}/questions")
async def get_question_statistics(
    quiz_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """Get statistics for each question in a quiz."""
    service = QuizAnalyticsService(db)
    return await service.get_question_statistics(quiz_id)
