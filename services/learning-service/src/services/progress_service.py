"""
PANDORA Learning Service - Progress Tracking Service
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Sequence

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import (
    LearningPath,
    Module,
    PathLesson,
    UserProgress,
    UserLearningStats,
    LearningPathEnrollment,
    LearningPathStatus,
    ModuleStatus,
    LessonStatus,
    ProgressStatus,
)
from src.core.logging import get_logger

logger = get_logger(__name__)


class ProgressTrackingService:
    """Service for tracking learning progress."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def track_lesson_progress(
        self,
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        learning_path_id: uuid.UUID | None = None,
        progress_percentage: float | None = None,
        time_spent_seconds: int | None = None,
        status: str | None = None,
        score: float | None = None,
        quiz_results: dict | None = None,
    ) -> UserProgress:
        """
        Track lesson progress for a user.
        
        Creates or updates progress record and recalculates module/path progress.
        """
        # Find or create progress record
        query = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id == lesson_id,
            )
        )
        result = await self.db.execute(query)
        progress = result.scalar_one_or_none()

        is_new = False
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                learning_path_id=learning_path_id,
                status=ProgressStatus.NOT_STARTED,
                progress_percentage=0.0,
                time_spent_seconds=0,
            )
            self.db.add(progress)
            is_new = True

        # Update fields
        if progress_percentage is not None:
            progress.progress_percentage = progress_percentage

        if time_spent_seconds is not None:
            progress.time_spent_seconds += time_spent_seconds

        if status:
            new_status = ProgressStatus(status)
            progress.status = new_status

            if new_status == ProgressStatus.IN_PROGRESS and not progress.started_at:
                progress.started_at = datetime.now(timezone.utc)
            elif new_status == ProgressStatus.COMPLETED:
                progress.completed_at = datetime.now(timezone.utc)
                progress.progress_percentage = 100.0

        if score is not None:
            progress.score = score
            progress.points_earned = int(score) if score else 0

        if quiz_results is not None:
            progress.quiz_results = quiz_results

        progress.updated_at = datetime.now(timezone.utc)
        progress.last_accessed_at = datetime.now(timezone.utc)

        await self.db.flush()

        # Recalculate module progress
        if learning_path_id:
            await self._recalculate_module_progress(learning_path_id, user_id)
            await self._update_enrollment_progress(learning_path_id, user_id)
            await self._update_user_stats(user_id)

        # Update streak
        await self.update_streak(user_id)

        logger.info(
            "progress_tracked",
            user_id=str(user_id),
            lesson_id=str(lesson_id),
            status=progress.status.value,
            percentage=progress.progress_percentage,
        )

        return progress

    async def calculate_module_progress(
        self,
        module_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[float, int, int]:
        """
        Calculate module progress for a user.
        
        Returns: (progress_percentage, completed_lessons, total_lessons)
        """
        # Get module with lessons
        query = select(Module).where(Module.id == module_id).options(
            selectinload(Module.lessons)
        )
        result = await self.db.execute(query)
        module = result.scalar_one_or_none()

        if not module:
            return 0.0, 0, 0

        total_lessons = len(module.lessons)
        if total_lessons == 0:
            return 0.0, 0, 0

        # Get progress for all lessons
        lesson_ids = [l.id for l in module.lessons]
        query = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.lesson_id.in_(lesson_ids),
            )
        )
        result = await self.db.execute(query)
        progress_records = result.scalars().all()

        completed = sum(
            1 for p in progress_records
            if p.status == ProgressStatus.COMPLETED
        )

        progress_pct = (completed / total_lessons) * 100
        return progress_pct, completed, total_lessons

    async def calculate_path_progress(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[float, int, int, int, int]:
        """
        Calculate learning path progress for a user.
        
        Returns: (progress_percentage, completed_lessons, total_lessons, 
                  completed_modules, total_modules)
        """
        # Get path with modules and lessons
        query = select(LearningPath).where(LearningPath.id == path_id).options(
            selectinload(LearningPath.modules).selectinload(Module.lessons)
        )
        result = await self.db.execute(query)
        path = result.scalar_one_or_none()

        if not path:
            return 0.0, 0, 0, 0, 0

        total_modules = len(path.modules)
        total_lessons = 0
        completed_lessons = 0
        completed_modules = 0

        for module in path.modules:
            total_lessons += len(module.lessons)

            # Get progress for module lessons
            lesson_ids = [l.id for l in module.lessons]
            if lesson_ids:
                query = select(UserProgress).where(
                    and_(
                        UserProgress.user_id == user_id,
                        UserProgress.lesson_id.in_(lesson_ids),
                    )
                )
                result = await self.db.execute(query)
                module_progress = result.scalars().all()

                module_completed = sum(
                    1 for p in module_progress
                    if p.status == ProgressStatus.COMPLETED
                )
                completed_lessons += module_completed

                if module_completed == len(module.lessons) and len(module.lessons) > 0:
                    completed_modules += 1

        progress_pct = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0.0
        return progress_pct, completed_lessons, total_lessons, completed_modules, total_modules

    async def update_streak(self, user_id: uuid.UUID) -> tuple[int, int]:
        """
        Update user's learning streak.
        
        Returns: (current_streak_days, longest_streak_days)
        """
        # Get or create user stats
        query = select(UserLearningStats).where(
            UserLearningStats.user_id == user_id
        )
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()

        if not stats:
            stats = UserLearningStats(
                user_id=user_id,
                current_streak_days=0,
                longest_streak_days=0,
            )
            self.db.add(stats)
            await self.db.flush()

        today = datetime.now(timezone.utc).date()

        # Check if there's activity today
        if stats.last_activity_at:
            last_activity = stats.last_activity_at.date()
            days_diff = (today - last_activity).days

            if days_diff == 0:
                # Already active today, no change
                pass
            elif days_diff == 1:
                # Consecutive day, increment streak
                stats.current_streak_days += 1
                if stats.current_streak_days > stats.longest_streak_days:
                    stats.longest_streak_days = stats.current_streak_days
            else:
                # Streak broken, reset
                stats.current_streak_days = 1
        else:
            # First activity
            stats.current_streak_days = 1
            stats.longest_streak_days = max(stats.longest_streak_days, 1)

        stats.last_activity_at = datetime.now(timezone.utc)
        stats.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        return stats.current_streak_days, stats.longest_streak_days

    async def _recalculate_module_progress(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Recalculate and update module progress for a path."""
        # Get path with modules
        query = select(LearningPath).where(LearningPath.id == path_id).options(
            selectinload(LearningPath.modules).selectinload(Module.lessons)
        )
        result = await self.db.execute(query)
        path = result.scalar_one_or_none()

        if not path:
            return

        for module in path.modules:
            pct, completed, total = await self.calculate_module_progress(module.id, user_id)
            module.progress_percentage = pct
            module.lesson_count = total

            if completed == total and total > 0:
                module.status = ModuleStatus.COMPLETED
                module.completed_at = datetime.now(timezone.utc)
            elif completed > 0:
                module.status = ModuleStatus.IN_PROGRESS

        await self.db.flush()

    async def _update_enrollment_progress(
        self,
        path_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Update enrollment progress for user."""
        query = select(LearningPathEnrollment).where(
            and_(
                LearningPathEnrollment.user_id == user_id,
                LearningPathEnrollment.learning_path_id == path_id,
            )
        )
        result = await self.db.execute(query)
        enrollment = result.scalar_one_or_none()

        if enrollment:
            progress_pct, _, _, _, _ = await self.calculate_path_progress(path_id, user_id)
            enrollment.progress_percentage = progress_pct

            if progress_pct == 100.0:
                enrollment.is_completed = True
                enrollment.completed_at = datetime.now(timezone.utc)
            elif progress_pct > 0 and not enrollment.started_at:
                enrollment.started_at = datetime.now(timezone.utc)

            enrollment.last_accessed_at = datetime.now(timezone.utc)
            await self.db.flush()

    async def _update_user_stats(self, user_id: uuid.UUID) -> None:
        """Update aggregated user learning statistics."""
        # Get or create stats
        query = select(UserLearningStats).where(
            UserLearningStats.user_id == user_id
        )
        result = await self.db.execute(query)
        stats = result.scalar_one_or_none()

        if not stats:
            stats = UserLearningStats(user_id=user_id)
            self.db.add(stats)
            await self.db.flush()

        # Get all progress records
        query = select(UserProgress).where(UserProgress.user_id == user_id)
        result = await self.db.execute(query)
        all_progress = result.scalars().all()

        # Calculate stats
        stats.lessons_completed = sum(
            1 for p in all_progress
            if p.status == ProgressStatus.COMPLETED
        )

        stats.total_time_seconds = sum(
            p.time_spent_seconds for p in all_progress
        )

        # Calculate average score
        scores = [p.score for p in all_progress if p.score is not None]
        if scores:
            stats.average_score = sum(scores) / len(scores)
            stats.highest_score = max(scores)

        # Count quizzes
        stats.quizzes_passed = sum(
            1 for p in all_progress
            if p.quiz_results and p.quiz_results.get("passed")
        )
        stats.quizzes_failed = sum(
            1 for p in all_progress
            if p.quiz_results and not p.quiz_results.get("passed")
        )

        # Count XP from completed lessons
        stats.total_xp = sum(
            p.points_earned for p in all_progress
        )

        # Count enrollments
        enroll_query = select(func.count()).select_from(LearningPathEnrollment).where(
            LearningPathEnrollment.user_id == user_id
        )
        enroll_result = await self.db.execute(enroll_query)
        stats.paths_enrolled = enroll_result.scalar() or 0

        stats.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def get_user_stats(self, user_id: uuid.UUID) -> UserLearningStats | None:
        """Get user's learning statistics."""
        query = select(UserLearningStats).where(
            UserLearningStats.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_recent_activity(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> list[UserProgress]:
        """Get user's recent learning activity."""
        query = (
            select(UserProgress)
            .where(UserProgress.user_id == user_id)
            .order_by(UserProgress.last_accessed_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
