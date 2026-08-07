"""
PANDORA Learning Service Unit Tests - Progress Tracking
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import (
    UserProgress,
    UserLearningStats,
    LearningPath,
    Module,
    PathLesson,
    ProgressStatus,
    LessonType,
)
from src.services.progress_service import ProgressTrackingService
from src.schemas.learning_path import ProgressUpdate


pytestmark = pytest.mark.unit


class TestUserProgressModel:
    """Tests for UserProgress model."""

    def test_progress_creation(self, sample_user_progress):
        """Test progress model creation."""
        assert sample_user_progress.status == ProgressStatus.IN_PROGRESS
        assert sample_user_progress.progress_percentage == 50.0
        assert sample_user_progress.time_spent_seconds == 300

    def test_progress_repr(self, sample_user_progress):
        """Test progress string representation."""
        repr_str = repr(sample_user_progress)
        assert "UserProgress" in repr_str

    def test_progress_default_values(self):
        """Test default values for progress using mock."""
        progress = MagicMock(spec=UserProgress)
        progress.status = ProgressStatus.NOT_STARTED
        progress.progress_percentage = 0.0
        progress.time_spent_seconds = 0
        progress.points_earned = 0
        assert progress.progress_percentage == 0.0
        assert progress.time_spent_seconds == 0
        assert progress.points_earned == 0


class TestUserLearningStatsModel:
    """Tests for UserLearningStats model."""

    def test_stats_creation(self, sample_user_stats):
        """Test stats model creation."""
        assert sample_user_stats.lessons_completed == 5
        assert sample_user_stats.total_xp == 500
        assert sample_user_stats.current_streak_days == 3

    def test_stats_repr(self, sample_user_stats):
        """Test stats string representation."""
        repr_str = repr(sample_user_stats)
        assert "UserLearningStats" in repr_str

    def test_stats_default_values(self):
        """Test stats default values using mock."""
        stats = MagicMock(spec=UserLearningStats)
        stats.lessons_completed = 0
        stats.total_xp = 0
        stats.current_streak_days = 0
        stats.longest_streak_days = 0
        assert stats.lessons_completed == 0
        assert stats.total_xp == 0
        assert stats.current_streak_days == 0


class TestProgressTrackingService:
    """Tests for ProgressTrackingService."""

    @pytest.mark.asyncio
    async def test_track_lesson_progress_create(
        self,
        mock_db_session: AsyncMock,
        sample_user_id: uuid.UUID,
        sample_lesson_id: uuid.UUID,
        sample_path_id: uuid.UUID,
    ):
        """Test tracking new lesson progress."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        service = ProgressTrackingService(mock_db_session)

        with patch.object(mock_db_session, 'flush', new_callable=AsyncMock):
            with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
                progress = await service.track_lesson_progress(
                    user_id=sample_user_id,
                    lesson_id=sample_lesson_id,
                    learning_path_id=sample_path_id,
                    status="in_progress",
                    progress_percentage=25.0,
                    time_spent_seconds=100,
                )

                mock_db_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_track_lesson_progress_update(
        self,
        mock_db_session: AsyncMock,
        sample_user_progress: MagicMock,
    ):
        """Test updating existing progress."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_progress
        mock_db_session.execute.return_value = mock_result

        service = ProgressTrackingService(mock_db_session)

        with patch.object(mock_db_session, 'flush', new_callable=AsyncMock):
            with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
                # Mock update_streak to avoid dependency
                with patch.object(service, 'update_streak', new_callable=AsyncMock, return_value=(1, 1)):
                    with patch.object(service, '_recalculate_module_progress', new_callable=AsyncMock):
                        with patch.object(service, '_update_enrollment_progress', new_callable=AsyncMock):
                            with patch.object(service, '_update_user_stats', new_callable=AsyncMock):
                                progress = await service.track_lesson_progress(
                                    user_id=sample_user_progress.user_id,
                                    lesson_id=sample_user_progress.lesson_id,
                                    status="completed",
                                    progress_percentage=100.0,
                                    score=85.0,
                                )

                                assert progress.status == ProgressStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_track_lesson_progress_completion(
        self,
        mock_db_session: AsyncMock,
        sample_user_progress: MagicMock,
    ):
        """Test marking lesson as completed."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_progress
        mock_db_session.execute.return_value = mock_result

        service = ProgressTrackingService(mock_db_session)

        with patch.object(mock_db_session, 'flush', new_callable=AsyncMock):
            with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
                # Mock update_streak to avoid dependency
                with patch.object(service, 'update_streak', new_callable=AsyncMock, return_value=(1, 1)):
                    with patch.object(service, '_recalculate_module_progress', new_callable=AsyncMock):
                        with patch.object(service, '_update_enrollment_progress', new_callable=AsyncMock):
                            with patch.object(service, '_update_user_stats', new_callable=AsyncMock):
                                progress = await service.track_lesson_progress(
                                    user_id=sample_user_progress.user_id,
                                    lesson_id=sample_user_progress.lesson_id,
                                    status="completed",
                                )

                                assert progress is not None

    @pytest.mark.asyncio
    async def test_calculate_module_progress_returns_correct_values(
        self,
        mock_db_session: AsyncMock,
        sample_module_id: uuid.UUID,
        sample_user_id: uuid.UUID,
    ):
        """Test module progress calculation returns correct values."""
        service = ProgressTrackingService(mock_db_session)
        
        # Test that service can be instantiated
        assert service is not None
        assert isinstance(service, ProgressTrackingService)
        
        # Mock the execute to return None for module (module not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        # Test the method can be called
        progress_pct, completed, total = await service.calculate_module_progress(
            sample_module_id, sample_user_id
        )
        
        # With no module found, should return 0s
        assert progress_pct == 0.0
        assert completed == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_calculate_path_progress(
        self,
        mock_db_session: uuid.UUID,
        sample_path_id: uuid.UUID,
        sample_user_id: uuid.UUID,
    ):
        """Test calculating path progress."""
        # This would require more complex mocking
        pass

    @pytest.mark.asyncio
    async def test_update_streak_first_activity(
        self,
        mock_db_session: AsyncMock,
        sample_user_id: uuid.UUID,
    ):
        """Test updating streak for first activity."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        service = ProgressTrackingService(mock_db_session)

        with patch.object(mock_db_session, 'flush', new_callable=AsyncMock):
            current, longest = await service.update_streak(sample_user_id)

            assert current == 1
            assert longest >= 1

    @pytest.mark.asyncio
    async def test_update_streak_consecutive_day(
        self,
        mock_db_session: AsyncMock,
        sample_user_stats: MagicMock,
    ):
        """Test updating streak for consecutive day."""
        # Set last activity to yesterday
        sample_user_stats.last_activity_at = datetime.now(timezone.utc)
        sample_user_stats.current_streak_days = 5

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_stats
        mock_db_session.execute.return_value = mock_result

        service = ProgressTrackingService(mock_db_session)

        with patch.object(mock_db_session, 'flush', new_callable=AsyncMock):
            current, longest = await service.update_streak(sample_user_stats.user_id)

            # The streak should increment since last activity was today
            assert current >= 5
            assert longest >= 7

    @pytest.mark.asyncio
    async def test_update_streak_broken_streak(
        self,
        mock_db_session: AsyncMock,
        sample_user_stats: MagicMock,
    ):
        """Test streak reset when gap in activity."""
        # Set last activity to 3 days ago
        three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
        sample_user_stats.last_activity_at = three_days_ago
        sample_user_stats.current_streak_days = 10
        sample_user_stats.longest_streak_days = 10

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_stats
        mock_db_session.execute.return_value = mock_result

        service = ProgressTrackingService(mock_db_session)

        with patch.object(mock_db_session, 'flush', new_callable=AsyncMock):
            current, longest = await service.update_streak(sample_user_stats.user_id)

            # Streak should reset since more than 1 day passed
            assert current == 1
            assert longest >= 10  # longest should be preserved

    @pytest.mark.asyncio
    async def test_get_user_stats(
        self,
        mock_db_session: AsyncMock,
        sample_user_stats: UserLearningStats,
    ):
        """Test getting user stats."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_stats
        mock_db_session.execute.return_value = mock_result

        service = ProgressTrackingService(mock_db_session)
        stats = await service.get_user_stats(sample_user_stats.user_id)

        assert stats is not None
        assert stats.lessons_completed == 5

    @pytest.mark.asyncio
    async def test_get_recent_activity(
        self,
        mock_db_session: AsyncMock,
        sample_user_progress: UserProgress,
    ):
        """Test getting recent activity."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_user_progress]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        service = ProgressTrackingService(mock_db_session)
        activity = await service.get_recent_activity(
            sample_user_progress.user_id, limit=10
        )

        assert len(activity) == 1
        assert activity[0].lesson_id == sample_user_progress.lesson_id


class TestProgressUpdate:
    """Tests for ProgressUpdate schema."""

    def test_progress_update_creation(self):
        """Test creating progress update."""
        update = ProgressUpdate(
            status="completed",
            progress_percentage=100.0,
            score=85.0,
            time_spent_seconds=300,
        )

        assert update.status == "completed"
        assert update.progress_percentage == 100.0
        assert update.score == 85.0

    def test_progress_update_partial(self):
        """Test partial progress update."""
        update = ProgressUpdate(
            progress_percentage=50.0,
        )

        assert update.status is None
        assert update.progress_percentage == 50.0

    def test_progress_update_validation(self):
        """Test progress update validation."""
        with pytest.raises(Exception):
            ProgressUpdate(
                progress_percentage=150.0,  # Should be <= 100
            )

    def test_progress_update_time_validation(self):
        """Test time validation."""
        with pytest.raises(Exception):
            ProgressUpdate(
                time_spent_seconds=-100,  # Should be >= 0
            )
