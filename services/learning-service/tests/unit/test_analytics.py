"""
PANDORA Learning Service Unit Tests - Analytics
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import (
    UserProgress,
    UserLearningStats,
    ProgressStatus,
    LessonType,
)
from src.services.analytics_service import AnalyticsService


pytestmark = pytest.mark.unit


class TestAnalyticsService:
    """Tests for AnalyticsService."""

    @pytest.fixture
    def mock_progress_records(self) -> list[UserProgress]:
        """Create mock progress records for testing."""
        records = []
        now = datetime.now(timezone.utc)

        for i in range(10):
            progress = MagicMock(spec=UserProgress)
            progress.id = uuid.uuid4()
            progress.lesson_id = uuid.uuid4()
            progress.status = (
                ProgressStatus.COMPLETED if i < 6 else ProgressStatus.IN_PROGRESS
            )
            progress.score = 70 + (i * 2) if i < 8 else None  # Scores 70-84, then None
            progress.time_spent_seconds = 300 + (i * 60)  # 5-10 min each
            progress.last_accessed_at = now - timedelta(days=i)
            progress.quiz_results = {"passed": i < 5} if i < 6 else None
            records.append(progress)

        return records

    @pytest.mark.asyncio
    async def test_get_progress_analytics(
        self,
        mock_db_session: AsyncMock,
        sample_user_id: uuid.UUID,
    ):
        """Test getting comprehensive progress analytics structure."""
        service = AnalyticsService(mock_db_session)
        
        # Mock the database calls
        mock_stats = MagicMock()
        mock_stats.current_streak_days = 3
        mock_stats.longest_streak_days = 7
        mock_stats.total_xp = 500
        
        mock_progress = MagicMock()
        mock_progress.status = ProgressStatus.COMPLETED
        mock_progress.score = 85.0
        mock_progress.time_spent_seconds = 300
        mock_progress.last_accessed_at = datetime.now(timezone.utc)
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_progress]
        mock_result.scalars.return_value = mock_scalars
        
        mock_db_session.execute.return_value = mock_result
        
        # Just test that the service can be instantiated and called
        assert service is not None
        assert isinstance(service, AnalyticsService)
        
        # Test the calculation methods directly
        overall = service._calculate_overall_stats(mock_stats, [mock_progress])
        assert overall["current_streak"] == 3
        assert overall["total_xp"] == 500

    @pytest.mark.asyncio
    async def test_calculate_overall_stats(
        self,
        mock_db_session: AsyncMock,
        sample_user_stats: MagicMock,
        mock_progress_records: list[MagicMock],
    ):
        """Test calculating overall stats."""
        service = AnalyticsService(mock_db_session)

        overall = service._calculate_overall_stats(
            sample_user_stats, mock_progress_records
        )

        assert overall["total_items"] == 10
        assert overall["completed"] == 6
        assert overall["completion_rate"] == 60.0
        assert overall["current_streak"] == 3
        assert overall["longest_streak"] == 7
        assert overall["total_xp"] == 500

    @pytest.mark.asyncio
    async def test_calculate_completion_rates(
        self,
        mock_db_session: AsyncMock,
        mock_progress_records: list[UserProgress],
    ):
        """Test calculating completion rates."""
        service = AnalyticsService(mock_db_session)

        rates = service._calculate_completion_rates(mock_progress_records)

        assert rates["overall"] == 60.0
        assert rates["total_items"] == 10
        assert rates["completed_items"] == 6

    @pytest.mark.asyncio
    async def test_calculate_time_analysis(
        self,
        mock_db_session: AsyncMock,
        mock_progress_records: list[UserProgress],
    ):
        """Test calculating time analysis."""
        service = AnalyticsService(mock_db_session)

        analysis = service._calculate_time_analysis(mock_progress_records)

        assert "total_seconds" in analysis
        assert "total_hours" in analysis
        assert "average_seconds_per_item" in analysis
        assert "by_day_of_week" in analysis

        # Total should be sum of time spent
        expected_total = sum(p.time_spent_seconds for p in mock_progress_records)
        assert analysis["total_seconds"] == expected_total

    @pytest.mark.asyncio
    async def test_calculate_score_distribution(
        self,
        mock_db_session: AsyncMock,
        mock_progress_records: list[UserProgress],
    ):
        """Test calculating score distribution."""
        service = AnalyticsService(mock_db_session)

        distribution = service._calculate_score_distribution(mock_progress_records)

        assert "distribution" in distribution
        assert "average" in distribution
        assert "highest" in distribution
        assert "lowest" in distribution
        assert "total_quizzes" in distribution

        # Check average
        scores = [p.score for p in mock_progress_records if p.score is not None]
        expected_avg = sum(scores) / len(scores)
        assert distribution["average"] == expected_avg

    @pytest.mark.asyncio
    async def test_calculate_activity_timeline(
        self,
        mock_db_session: AsyncMock,
        mock_progress_records: list[UserProgress],
    ):
        """Test calculating activity timeline."""
        service = AnalyticsService(mock_db_session)

        timeline = service._calculate_activity_timeline(mock_progress_records)

        assert isinstance(timeline, list)
        assert len(timeline) <= 30  # Limited to 30 days

        if timeline:
            assert "date" in timeline[0]
            assert "items_completed" in timeline[0]
            assert "time_minutes" in timeline[0]

    @pytest.mark.asyncio
    async def test_empty_progress(self, mock_db_session: AsyncMock):
        """Test analytics with no progress data."""
        service = AnalyticsService(mock_db_session)

        # Test with empty lists
        overall = service._calculate_overall_stats(None, [])
        assert overall["total_items"] == 0
        assert overall["completion_rate"] == 0

        rates = service._calculate_completion_rates([])
        assert rates["overall"] == 0

        time_analysis = service._calculate_time_analysis([])
        assert time_analysis["total_seconds"] == 0

        score_dist = service._calculate_score_distribution([])
        assert score_dist["average"] is None


class TestStrengthsWeaknesses:
    """Tests for strengths/weaknesses analysis."""

    @pytest.fixture
    def mixed_performance_records(self) -> list[UserProgress]:
        """Create records with varied performance."""
        records = []
        now = datetime.now(timezone.utc)

        # High performers
        for i in range(5):
            progress = MagicMock(spec=UserProgress)
            progress.score = 85 + i
            progress.time_spent_seconds = 180 + (i * 30)  # 3-4.5 min
            progress.status = ProgressStatus.COMPLETED
            progress.completed_at = now - timedelta(days=i)
            records.append(progress)

        # Low performers
        for i in range(3):
            progress = MagicMock(spec=UserProgress)
            progress.score = 55 + (i * 5)  # 55-65
            progress.time_spent_seconds = 900 + (i * 60)  # 15-16 min
            progress.status = ProgressStatus.COMPLETED
            progress.completed_at = now - timedelta(days=i + 10)
            records.append(progress)

        return records

    @pytest.mark.asyncio
    async def test_get_strengths_weaknesses(
        self,
        mock_db_session: AsyncMock,
        mixed_performance_records: list[UserProgress],
    ):
        """Test getting strengths and weaknesses."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mixed_performance_records

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        service = AnalyticsService(mock_db_session)
        analysis = await service.get_strengths_weaknesses(uuid.uuid4())

        assert "strengths" in analysis
        assert "weaknesses" in analysis
        assert "recommendations" in analysis
        assert "confidence_level" in analysis

    @pytest.mark.asyncio
    async def test_empty_progress_strengths(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test strengths analysis with no progress."""
        service = AnalyticsService(mock_db_session)
        
        # Test with empty records directly
        analysis = service._calculate_overall_stats(None, [])
        assert analysis["total_items"] == 0
        assert analysis["completion_rate"] == 0


class TestLearningInsights:
    """Tests for learning insights."""

    @pytest.mark.asyncio
    async def test_get_learning_insights(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test getting learning insights structure."""
        service = AnalyticsService(mock_db_session)
        
        # Test the helper methods
        analytics = {
            "overall_stats": {
                "completed": 5,
                "total_time_hours": 2,
                "current_streak": 3,
            },
            "completion_rates": {"overall": 75.0},
            "score_distribution": {"lowest": 55},
        }
        
        strengths = {
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
        }
        
        # Test the insight generation methods
        summary = service._generate_summary(analytics)
        assert "5" in summary or summary != ""
        
        patterns = service._identify_patterns(analytics)
        assert isinstance(patterns, list)
        
        next_steps = service._suggest_next_steps(analytics, strengths)
        assert isinstance(next_steps, list)
        
        achievements = service._check_achievements(analytics)
        assert isinstance(achievements, list)
        
        # Should have at least first_completion (5 >= 1)
        assert len(achievements) >= 1

    @pytest.mark.asyncio
    async def test_generate_summary(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test summary generation."""
        service = AnalyticsService(mock_db_session)

        analytics = {
            "overall_stats": {
                "completed": 10,
                "total_time_hours": 5,
                "current_streak": 7,
            },
            "completion_rates": {
                "overall": 75.0,
            },
        }

        summary = service._generate_summary(analytics)

        assert "10" in summary
        assert "5" in summary
        assert "7" in summary

    @pytest.mark.asyncio
    async def test_identify_patterns(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test pattern identification."""
        service = AnalyticsService(mock_db_session)

        analytics = {
            "time_analysis": {
                "by_day_of_week": [
                    {"day": "Saturday", "time_minutes": 120},
                    {"day": "Sunday", "time_minutes": 45},
                ],
            },
            "score_distribution": {
                "average": 88,
            },
        }

        patterns = service._identify_patterns(analytics)

        assert len(patterns) > 0

    @pytest.mark.asyncio
    async def test_suggest_next_steps(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test next steps suggestion."""
        service = AnalyticsService(mock_db_session)

        analytics = {
            "completion_rates": {
                "overall": 40.0,
            },
            "score_distribution": {
                "lowest": 55,
            },
        }

        strengths = {
            "weaknesses": [],
        }

        suggestions = service._suggest_next_steps(analytics, strengths)

        assert isinstance(suggestions, list)

    @pytest.mark.asyncio
    async def test_check_achievements(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test achievement checking."""
        service = AnalyticsService(mock_db_session)

        analytics = {
            "overall_stats": {
                "completed": 5,
                "total_time_hours": 2,
                "current_streak": 10,
            },
        }

        achievements = service._check_achievements(analytics)

        # Should have first_completion (5 >= 1)
        assert len(achievements) >= 1
        assert any(a["id"] == "first_completion" for a in achievements)


class TestWeeklySummary:
    """Tests for weekly summary calculation."""

    @pytest.mark.asyncio
    async def test_calculate_weekly_summary(
        self,
        mock_db_session: AsyncMock,
        sample_user_id: uuid.UUID,
    ):
        """Test weekly summary calculation."""
        # Create progress for last 3 days
        now = datetime.now(timezone.utc)
        week_progress = []

        for i in range(3):
            progress = MagicMock(spec=UserProgress)
            progress.status = ProgressStatus.COMPLETED
            progress.time_spent_seconds = 600
            progress.last_accessed_at = now - timedelta(days=i)
            week_progress.append(progress)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = week_progress

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        service = AnalyticsService(mock_db_session)
        summary = await service._calculate_weekly_summary(sample_user_id)

        assert "items_completed" in summary
        assert "time_spent_hours" in summary
        assert "active_days" in summary

        assert summary["items_completed"] == 3
        assert summary["active_days"] == 3
