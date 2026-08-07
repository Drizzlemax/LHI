"""
PANDORA Learning Service - Analytics Service
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from collections import defaultdict

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    LearningPath,
    Module,
    PathLesson,
    UserProgress,
    UserLearningStats,
    LearningPathEnrollment,
    LessonType,
    ProgressStatus,
)
from src.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for learning analytics and insights."""

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db

    async def get_progress_analytics(
        self,
        user_id: uuid.UUID,
        path_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive progress analytics for a user.
        
        Returns detailed analytics including completion rates,
        time spent, score distribution, and learning patterns.
        """
        # Get user stats
        stats_query = select(UserLearningStats).where(
            UserLearningStats.user_id == user_id
        )
        stats_result = await self.db.execute(stats_query)
        stats = stats_result.scalar_one_or_none()

        # Get all progress
        query = select(UserProgress).where(UserProgress.user_id == user_id)
        if path_id:
            query = query.where(UserProgress.learning_path_id == path_id)
        result = await self.db.execute(query)
        all_progress = list(result.scalars().all())

        # Calculate analytics
        analytics = {
            "user_id": str(user_id),
            "learning_path_id": str(path_id) if path_id else None,
            "overall_stats": self._calculate_overall_stats(stats, all_progress),
            "completion_rates": self._calculate_completion_rates(all_progress),
            "time_analysis": self._calculate_time_analysis(all_progress),
            "score_distribution": self._calculate_score_distribution(all_progress),
            "activity_timeline": self._calculate_activity_timeline(all_progress),
            "lesson_type_performance": await self._calculate_lesson_type_performance(all_progress),
            "weekly_summary": await self._calculate_weekly_summary(user_id),
        }

        return analytics

    def _calculate_overall_stats(
        self,
        stats: UserLearningStats | None,
        progress: list[UserProgress],
    ) -> dict[str, Any]:
        """Calculate overall learning statistics."""
        total_items = len(progress)
        completed = sum(1 for p in progress if p.status == ProgressStatus.COMPLETED)
        in_progress = sum(1 for p in progress if p.status == ProgressStatus.IN_PROGRESS)

        total_time = sum(p.time_spent_seconds for p in progress)
        hours_spent = total_time / 3600

        scores = [p.score for p in progress if p.score is not None]
        avg_score = sum(scores) / len(scores) if scores else None

        return {
            "total_items": total_items,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": total_items - completed - in_progress,
            "completion_rate": (completed / total_items * 100) if total_items > 0 else 0,
            "total_time_hours": round(hours_spent, 2),
            "average_score": round(avg_score, 1) if avg_score else None,
            "current_streak": stats.current_streak_days if stats else 0,
            "longest_streak": stats.longest_streak_days if stats else 0,
            "total_xp": stats.total_xp if stats else 0,
        }

    def _calculate_completion_rates(
        self,
        progress: list[UserProgress],
    ) -> dict[str, Any]:
        """Calculate completion rates by different dimensions."""
        if not progress:
            return {"overall": 0, "by_type": {}, "weekly_trend": []}

        total = len(progress)
        completed = sum(1 for p in progress if p.status == ProgressStatus.COMPLETED)

        # Completion by type (inferred from quiz_results presence)
        by_type = defaultdict(lambda: {"total": 0, "completed": 0})
        for p in progress:
            lesson_type = "quiz" if p.quiz_results else "content"
            by_type[lesson_type]["total"] += 1
            if p.status == ProgressStatus.COMPLETED:
                by_type[lesson_type]["completed"] += 1

        # Calculate percentages
        by_type_rates = {}
        for lesson_type, counts in by_type.items():
            rate = (counts["completed"] / counts["total"] * 100) if counts["total"] > 0 else 0
            by_type_rates[lesson_type] = {
                "completion_rate": round(rate, 1),
                "total": counts["total"],
                "completed": counts["completed"],
            }

        return {
            "overall": round((completed / total * 100), 1) if total > 0 else 0,
            "total_items": total,
            "completed_items": completed,
            "by_type": by_type_rates,
        }

    def _calculate_time_analysis(
        self,
        progress: list[UserProgress],
    ) -> dict[str, Any]:
        """Calculate time-based learning analytics."""
        if not progress:
            return {"total_seconds": 0, "average_per_item": 0, "by_day": []}

        total_seconds = sum(p.time_spent_seconds for p in progress)
        avg_seconds = total_seconds / len(progress) if progress else 0

        # Time by day of week
        time_by_day = defaultdict(int)
        for p in progress:
            if p.last_accessed_at:
                day = p.last_accessed_at.strftime("%A")
                time_by_day[day] += p.time_spent_seconds

        by_day = [
            {"day": day, "time_minutes": round(mins, 1)}
            for day, mins in time_by_day.items()
        ]

        return {
            "total_seconds": total_seconds,
            "total_hours": round(total_seconds / 3600, 2),
            "average_seconds_per_item": round(avg_seconds, 0),
            "average_minutes_per_item": round(avg_seconds / 60, 1),
            "by_day_of_week": by_day,
        }

    def _calculate_score_distribution(
        self,
        progress: list[UserProgress],
    ) -> dict[str, Any]:
        """Calculate score distribution."""
        scores = [p.score for p in progress if p.score is not None]

        if not scores:
            return {"distribution": [], "average": None, "highest": None, "lowest": None}

        # Create distribution buckets
        buckets = [
            ("0-20", 0, 20),
            ("21-40", 21, 40),
            ("41-60", 41, 60),
            ("61-80", 61, 80),
            ("81-100", 81, 100),
        ]

        distribution = []
        for label, low, high in buckets:
            count = sum(1 for s in scores if low <= s <= high)
            percentage = (count / len(scores) * 100) if scores else 0
            distribution.append({
                "range": label,
                "count": count,
                "percentage": round(percentage, 1),
            })

        return {
            "distribution": distribution,
            "average": round(sum(scores) / len(scores), 1),
            "highest": max(scores),
            "lowest": min(scores),
            "total_quizzes": len(scores),
        }

    def _calculate_activity_timeline(
        self,
        progress: list[UserProgress],
    ) -> list[dict[str, Any]]:
        """Calculate activity over time."""
        timeline: dict[str, dict] = defaultdict(lambda: {"items": 0, "time_seconds": 0})

        for p in progress:
            if p.last_accessed_at:
                date_key = p.last_accessed_at.strftime("%Y-%m-%d")
                timeline[date_key]["items"] += 1
                timeline[date_key]["time_seconds"] += p.time_spent_seconds

        # Sort and limit to last 30 days
        sorted_dates = sorted(timeline.items(), key=lambda x: x[0], reverse=True)[:30]

        return [
            {
                "date": date,
                "items_completed": data["items"],
                "time_minutes": round(data["time_seconds"] / 60, 1),
            }
            for date, data in sorted_dates
        ]

    async def _calculate_lesson_type_performance(
        self,
        progress: list[UserProgress],
    ) -> dict[str, Any]:
        """Calculate performance by lesson type."""
        by_type: dict[str, dict] = {}

        for lesson_type in LessonType:
            # Get lessons of this type
            type_query = select(PathLesson).where(
                PathLesson.lesson_type == lesson_type
            )
            type_result = await self.db.execute(type_query)
            lessons = list(type_result.scalars().all())
            lesson_ids = [l.id for l in lessons]

            if not lesson_ids:
                continue

            # Get progress for these lessons
            type_progress = [p for p in progress if p.lesson_id in lesson_ids]
            if not type_progress:
                continue

            completed = sum(1 for p in type_progress if p.status == ProgressStatus.COMPLETED)
            total_time = sum(p.time_spent_seconds for p in type_progress)
            scores = [p.score for p in type_progress if p.score is not None]

            by_type[lesson_type.value] = {
                "total": len(type_progress),
                "completed": completed,
                "completion_rate": round((completed / len(type_progress) * 100), 1) if type_progress else 0,
                "average_time_minutes": round(total_time / len(type_progress) / 60, 1) if type_progress else 0,
                "average_score": round(sum(scores) / len(scores), 1) if scores else None,
            }

        return by_type

    async def _calculate_weekly_summary(
        self,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Calculate weekly learning summary."""
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        query = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.last_accessed_at >= week_ago,
            )
        )
        result = await self.db.execute(query)
        week_progress = list(result.scalars().all())

        completed = sum(1 for p in week_progress if p.status == ProgressStatus.COMPLETED)
        total_time = sum(p.time_spent_seconds for p in week_progress)

        return {
            "items_completed": completed,
            "time_spent_hours": round(total_time / 3600, 2),
            "active_days": len(set(
                p.last_accessed_at.strftime("%Y-%m-%d")
                for p in week_progress
                if p.last_accessed_at
            )),
            "comparison_to_previous_week": "increase",  # TODO: Calculate properly
        }

    async def get_strengths_weaknesses(
        self,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Analyze user's strengths and weaknesses.
        
        Identifies areas where user excels and areas needing improvement
        based on performance across different content categories and lesson types.
        """
        # Get all progress with lesson info
        query = select(UserProgress).where(
            and_(
                UserProgress.user_id == user_id,
                UserProgress.status == ProgressStatus.COMPLETED,
            )
        ).order_by(UserProgress.completed_at.desc())
        result = await self.db.execute(query)
        completed = list(result.scalars().all())

        if not completed:
            return {
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
            }

        # Analyze by implicit categories (based on content patterns)
        strength_areas = []
        weakness_areas = []
        recommendations = []

        # Group by performance
        high_performers = [p for p in completed if p.score and p.score >= 85]
        low_performers = [p for p in completed if p.score and p.score < 70]

        # Quick learners (high score, low time)
        for p in completed:
            if p.score and p.time_spent_seconds:
                efficiency = p.score / (p.time_spent_seconds / 60)  # score per minute
                if p.score >= 80 and efficiency > 1.0:
                    strength_areas.append({
                        "type": "efficient_learner",
                        "evidence": f"High scores ({p.score}%) with quick completion",
                    })

        # Slow but thorough
        for p in completed:
            if p.score and p.time_spent_seconds > 1800:  # > 30 min
                if p.score >= 90:
                    weakness_areas.append({
                        "type": "slow_pacer",
                        "evidence": f"Taking {p.time_spent_seconds // 60} minutes for standard content",
                    })

        # Recommendations
        if len(completed) < 5:
            recommendations.append({
                "priority": "high",
                "action": "Complete more lessons",
                "reason": "Need at least 5 completed items for accurate analysis",
            })

        if any(p.score and p.score < 60 for p in completed[:10]):
            recommendations.append({
                "priority": "medium",
                "action": "Review fundamentals",
                "reason": "Some recent scores indicate gaps in foundational knowledge",
            })

        if completed and all(p.time_spent_seconds < 300 for p in completed[:5]):
            recommendations.append({
                "priority": "low",
                "action": "Slow down and absorb content",
                "reason": "Sessions are very short - may be rushing through material",
            })

        return {
            "strengths": strength_areas[:5],
            "weaknesses": weakness_areas[:5],
            "recommendations": recommendations,
            "confidence_level": min(len(completed) / 20, 1.0),  # More data = higher confidence
        }

    async def get_learning_insights(
        self,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Get AI-generated learning insights."""
        analytics = await self.get_progress_analytics(user_id)
        strengths = await self.get_strengths_weaknesses(user_id)

        insights = {
            "summary": self._generate_summary(analytics),
            "patterns": self._identify_patterns(analytics),
            "next_steps": self._suggest_next_steps(analytics, strengths),
            "achievements": self._check_achievements(analytics),
        }

        return insights

    def _generate_summary(self, analytics: dict) -> str:
        """Generate a human-readable summary."""
        overall = analytics.get("overall_stats", {})
        completion = analytics.get("completion_rates", {})

        parts = []
        if overall.get("completed", 0) > 0:
            parts.append(f"You've completed {overall['completed']} items")
        if overall.get("total_time_hours", 0) > 0:
            parts.append(f"and spent {overall['total_time_hours']} hours learning")
        if overall.get("current_streak", 0) > 0:
            parts.append(f"with a {overall['current_streak']}-day learning streak!")

        return ". ".join(parts) if parts else "Start your learning journey today!"

    def _identify_patterns(self, analytics: dict) -> list[dict[str, str]]:
        """Identify learning patterns."""
        patterns = []
        time_analysis = analytics.get("time_analysis", {})
        by_day = time_analysis.get("by_day_of_week", [])

        if by_day:
            most_active = max(by_day, key=lambda x: x["time_minutes"], default=None)
            if most_active and most_active["time_minutes"] > 60:
                patterns.append({
                    "pattern": "peak_day",
                    "description": f"You're most active on {most_active['day']}s",
                })

        score_dist = analytics.get("score_distribution", {})
        if score_dist.get("average"):
            if score_dist["average"] >= 85:
                patterns.append({
                    "pattern": "high_performer",
                    "description": "You consistently score in the excellent range",
                })
            elif score_dist["average"] < 70:
                patterns.append({
                    "pattern": "needs_review",
                    "description": "Consider reviewing material more thoroughly",
                })

        return patterns

    def _suggest_next_steps(
        self,
        analytics: dict,
        strengths: dict,
    ) -> list[dict[str, str]]:
        """Suggest next learning steps."""
        suggestions = []

        completion = analytics.get("completion_rates", {})
        if completion.get("overall", 0) < 50:
            suggestions.append({
                "action": "Focus on completion",
                "reason": "You have several items in progress",
            })

        score_dist = analytics.get("score_distribution", {})
        if score_dist.get("lowest") and score_dist["lowest"] < 60:
            suggestions.append({
                "action": "Retry low-scoring content",
                "reason": "Review material you scored below 60% on",
            })

        return suggestions

    def _check_achievements(self, analytics: dict) -> list[dict[str, str]]:
        """Check for unlocked achievements."""
        achievements = []
        overall = analytics.get("overall_stats", {})

        if overall.get("completed", 0) >= 1:
            achievements.append({
                "id": "first_completion",
                "name": "First Steps",
                "description": "Completed your first lesson",
            })

        if overall.get("total_time_hours", 0) >= 1:
            achievements.append({
                "id": "hour_learner",
                "name": "Hour Learner",
                "description": "Spent 1 hour learning",
            })

        if overall.get("current_streak", 0) >= 7:
            achievements.append({
                "id": "week_streak",
                "name": "Week Warrior",
                "description": "Maintained a 7-day learning streak",
            })

        return achievements
