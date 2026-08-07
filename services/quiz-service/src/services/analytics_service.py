"""
PANDORA Quiz Service Analytics Service
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Quiz, QuizSession, QuestionResponse, QuizAnalytics
from src.models import QuizSessionStatus
from src.schemas.analytics import ScoreDistribution, TimeAnalysis, PerformanceSummary


class QuizAnalyticsService:
    """Service for quiz analytics."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_quiz_analytics(
        self,
        quiz_id: uuid.UUID,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> QuizAnalytics | None:
        """Get analytics for a quiz."""
        query = select(QuizAnalytics).where(QuizAnalytics.quiz_id == quiz_id)
        
        if period_start:
            query = query.where(QuizAnalytics.period_start >= period_start)
        if period_end:
            query = query.where(QuizAnalytics.period_end <= period_end)
        
        query = query.order_by(QuizAnalytics.period_end.desc())
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def calculate_and_save_analytics(
        self,
        quiz_id: uuid.UUID,
        period_days: int = 30,
    ) -> QuizAnalytics:
        """Calculate and save quiz analytics."""
        quiz = await self._get_quiz(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz {quiz_id} not found")
        
        # Calculate period
        now = datetime.now(timezone.utc)
        period_end = now
        period_start = now - timedelta(days=period_days)
        
        # Get sessions
        sessions = await self._get_sessions_in_period(quiz_id, period_start, period_end)
        
        # Calculate statistics
        total_attempts = len(sessions)
        completed = [s for s in sessions if s.status == QuizSessionStatus.COMPLETED]
        completed_attempts = len(completed)
        
        # Score statistics
        scores = [s.percentage_score for s in completed if s.percentage_score is not None]
        
        avg_score = float(np.mean(scores)) if scores else 0.0
        median_score = float(np.median(scores)) if scores else None
        std_score = float(np.std(scores)) if len(scores) > 1 else None
        min_score = float(np.min(scores)) if scores else None
        max_score = float(np.max(scores)) if scores else None
        
        # Pass/fail
        pass_count = sum(1 for s in completed if s.passed)
        fail_count = completed_attempts - pass_count
        pass_rate = (pass_count / completed_attempts * 100) if completed_attempts > 0 else None
        
        # Time statistics
        times = [s.time_spent_seconds for s in completed if s.time_spent_seconds > 0]
        avg_time = float(np.mean(times)) if times else None
        median_time = float(np.median(times)) if times else None
        
        # Unique users
        user_ids = {s.user_id for s in sessions}
        unique_users = len(user_ids)
        
        analytics = QuizAnalytics(
            quiz_id=quiz_id,
            period_start=period_start,
            period_end=period_end,
            total_attempts=total_attempts,
            completed_attempts=completed_attempts,
            unique_users=unique_users,
            repeat_users=total_attempts - unique_users,
            average_score=avg_score,
            median_score=median_score,
            std_dev_score=std_score,
            min_score=min_score,
            max_score=max_score,
            pass_count=pass_count,
            fail_count=fail_count,
            pass_rate=pass_rate,
            average_time_seconds=avg_time,
            median_time_seconds=median_time,
        )
        
        self.db.add(analytics)
        await self.db.flush()
        await self.db.refresh(analytics)
        
        return analytics
    
    async def get_performance_summary(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> PerformanceSummary:
        """Get performance summary for a quiz."""
        # Get sessions
        query = select(QuizSession).where(QuizSession.quiz_id == quiz_id)
        
        if user_id:
            query = query.where(QuizSession.user_id == user_id)
        
        result = await self.db.execute(
            query.where(QuizSession.status == QuizSessionStatus.COMPLETED)
        )
        sessions = list(result.scalars().all())
        
        if not sessions:
            return PerformanceSummary(
                total_attempts=0,
                completed_attempts=0,
                average_score=0.0,
                pass_rate=0.0,
                average_time_minutes=0.0,
                score_distribution=ScoreDistribution(),
                time_analysis=TimeAnalysis(
                    average_time_seconds=0,
                    total_time_hours=0,
                ),
            )
        
        scores = [s.percentage_score for s in sessions if s.percentage_score is not None]
        times = [s.time_spent_seconds for s in sessions if s.time_spent_seconds > 0]
        
        # Score distribution
        dist = ScoreDistribution()
        for score in scores:
            if score <= 20:
                dist.range_0_20 += 1
            elif score <= 40:
                dist.range_20_40 += 1
            elif score <= 60:
                dist.range_40_60 += 1
            elif score <= 80:
                dist.range_60_80 += 1
            else:
                dist.range_80_100 += 1
        
        # Pass rate
        passed = sum(1 for s in sessions if s.passed)
        pass_rate = (passed / len(sessions) * 100) if sessions else 0.0
        
        return PerformanceSummary(
            total_attempts=len(sessions),
            completed_attempts=len(sessions),
            average_score=float(np.mean(scores)) if scores else 0.0,
            median_score=float(np.median(scores)) if scores else None,
            pass_rate=pass_rate,
            average_time_minutes=float(np.mean(times)) / 60 if times else 0.0,
            score_distribution=dist,
            time_analysis=TimeAnalysis(
                average_time_seconds=float(np.mean(times)) if times else 0.0,
                median_time_seconds=float(np.median(times)) if times else None,
                min_time_seconds=float(np.min(times)) if times else None,
                max_time_seconds=float(np.max(times)) if times else None,
                total_time_hours=sum(times) / 3600 if times else 0.0,
            ),
        )
    
    async def get_question_statistics(
        self,
        quiz_id: uuid.UUID,
    ) -> list[dict]:
        """Get statistics for each question in a quiz."""
        # Get all responses for the quiz
        result = await self.db.execute(
            select(QuestionResponse)
            .join(QuizSession, QuestionResponse.session_id == QuizSession.id)
            .where(QuizSession.quiz_id == quiz_id)
            .where(QuizSession.status == QuizSessionStatus.COMPLETED)
        )
        responses = list(result.scalars().all())
        
        # Group by question
        question_stats: dict[uuid.UUID, dict] = {}
        
        for response in responses:
            qid = response.question_id
            if qid not in question_stats:
                question_stats[qid] = {
                    "question_id": qid,
                    "times_shown": 0,
                    "times_correct": 0,
                    "p_value": 0.0,
                }
            
            stats = question_stats[qid]
            stats["times_shown"] += 1
            if response.is_correct:
                stats["times_correct"] += 1
        
        # Calculate p-values
        for qid, stats in question_stats.items():
            if stats["times_shown"] > 0:
                stats["p_value"] = stats["times_correct"] / stats["times_shown"]
        
        return list(question_stats.values())
    
    async def _get_quiz(self, quiz_id: uuid.UUID) -> Quiz | None:
        """Get quiz by ID."""
        result = await self.db.execute(
            select(Quiz).where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_sessions_in_period(
        self,
        quiz_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> list[QuizSession]:
        """Get quiz sessions in a time period."""
        result = await self.db.execute(
            select(QuizSession)
            .where(QuizSession.quiz_id == quiz_id)
            .where(QuizSession.started_at >= period_start)
            .where(QuizSession.started_at <= period_end)
        )
        return list(result.scalars().all())
