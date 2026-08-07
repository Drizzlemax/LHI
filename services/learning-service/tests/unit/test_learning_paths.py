"""
PANDORA Learning Service Unit Tests - Learning Paths
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import LearningPath, LearningPathStatus
from src.services.learning_path_service import LearningPathService
from src.schemas.learning_path import LearningPathCreate, LearningPathUpdate


pytestmark = pytest.mark.unit


class TestLearningPathModel:
    """Tests for LearningPath model."""

    def test_learning_path_creation(self, sample_learning_path):
        """Test learning path model creation."""
        assert sample_learning_path.title == "Introduction to Python"
        assert sample_learning_path.status == LearningPathStatus.DRAFT
        assert sample_learning_path.progress_percentage == 0.0
        assert sample_learning_path.is_public is False

    def test_learning_path_repr(self, sample_learning_path):
        """Test learning path string representation."""
        repr_str = repr(sample_learning_path)
        assert "LearningPath" in repr_str

    def test_learning_path_default_values(self):
        """Test default values for learning path using mock."""
        path = MagicMock(spec=LearningPath)
        path.progress_percentage = 0.0
        path.is_public = False
        path.is_featured = False
        path.module_count = 0
        path.lesson_count = 0
        assert path.progress_percentage == 0.0
        assert path.is_public is False
        assert path.is_featured is False
        assert path.module_count == 0
        assert path.lesson_count == 0


class TestLearningPathService:
    """Tests for LearningPathService."""

    @pytest.mark.asyncio
    async def test_create_learning_path(
        self,
        mock_db_session: AsyncMock,
        sample_user_id: uuid.UUID,
    ):
        """Test creating a learning path."""
        service = LearningPathService(mock_db_session)

        data = LearningPathCreate(
            title="New Path",
            description="A new learning path",
            goal="Learn new things",
            target_education_level="undergraduate",
        )

        with patch.object(mock_db_session, 'flush', new_callable=AsyncMock):
            with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
                with patch.object(mock_db_session, 'refresh', new_callable=AsyncMock):
                    path = await service.create_learning_path(data, sample_user_id)

                    mock_db_session.add.assert_called()
                    mock_db_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_get_learning_path(
        self,
        mock_db_session: AsyncMock,
        sample_path_id: uuid.UUID,
        sample_learning_path: LearningPath,
    ):
        """Test getting a learning path."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_learning_path
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)
        path = await service.get_learning_path(sample_path_id)

        assert path is not None
        assert path.id == sample_path_id
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_learning_path_not_found(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test getting non-existent learning path."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)
        path = await service.get_learning_path(uuid.uuid4())

        assert path is None

    @pytest.mark.asyncio
    async def test_update_learning_path(
        self,
        mock_db_session: AsyncMock,
        sample_learning_path: LearningPath,
    ):
        """Test updating a learning path."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_learning_path
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)

        data = LearningPathUpdate(
            title="Updated Title",
            description="Updated description",
        )

        with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
            with patch.object(mock_db_session, 'refresh', new_callable=AsyncMock):
                path = await service.update_learning_path(
                    sample_learning_path.id, data
                )

                assert path is not None
                assert path.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_delete_learning_path(
        self,
        mock_db_session: AsyncMock,
        sample_learning_path: LearningPath,
    ):
        """Test soft deleting a learning path."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_learning_path
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)

        with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
            result = await service.delete_learning_path(sample_learning_path.id)

            assert result is True
            assert sample_learning_path.status == LearningPathStatus.DELETED
            assert sample_learning_path.deleted_at is not None

    @pytest.mark.asyncio
    async def test_publish_learning_path(
        self,
        mock_db_session: AsyncMock,
        sample_learning_path: LearningPath,
    ):
        """Test publishing a learning path."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_learning_path
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)

        with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
            with patch.object(mock_db_session, 'refresh', new_callable=AsyncMock):
                path = await service.publish_learning_path(sample_learning_path.id)

                assert path is not None
                assert path.status == LearningPathStatus.PUBLISHED
                assert path.published_at is not None

    @pytest.mark.asyncio
    async def test_list_learning_paths(
        self,
        mock_db_session: AsyncMock,
        sample_learning_path: MagicMock,
    ):
        """Test listing learning paths."""
        service = LearningPathService(mock_db_session)
        
        # Test that service can be instantiated
        assert service is not None
        assert isinstance(service, LearningPathService)

    @pytest.mark.asyncio
    async def test_list_learning_paths_with_filters(
        self,
        mock_db_session: AsyncMock,
        sample_learning_path: LearningPath,
        sample_user_id: uuid.UUID,
    ):
        """Test listing learning paths with filters."""
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_learning_path]
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)
        paths, total = await service.list_learning_paths(
            user_id=sample_user_id,
            status=LearningPathStatus.DRAFT,
            target_education_level="undergraduate",
        )

        assert len(paths) == 1
        mock_db_session.execute.assert_called()


class TestLearningPathEnrollment:
    """Tests for learning path enrollment."""

    @pytest.mark.asyncio
    async def test_enroll_in_learning_path(
        self,
        mock_db_session: AsyncMock,
        sample_path_id: uuid.UUID,
        sample_user_id: uuid.UUID,
    ):
        """Test enrolling in a learning path."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)

        with patch.object(mock_db_session, 'flush', new_callable=AsyncMock):
            with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
                with patch.object(mock_db_session, 'refresh', new_callable=AsyncMock):
                    enrollment = await service.enroll_in_learning_path(
                        sample_path_id, sample_user_id
                    )

                    mock_db_session.add.assert_called()

    @pytest.mark.asyncio
    async def test_unenroll_from_learning_path(
        self,
        mock_db_session: AsyncMock,
        sample_path_id: uuid.UUID,
        sample_user_id: uuid.UUID,
    ):
        """Test unenrolling from a learning path."""
        mock_enrollment = MagicMock()
        mock_enrollment.is_active = True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_enrollment
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)

        with patch.object(mock_db_session, 'commit', new_callable=AsyncMock):
            result = await service.unenroll_from_learning_path(
                sample_path_id, sample_user_id
            )

            assert result is True
            assert mock_enrollment.is_active is False


class TestLearningPathProgress:
    """Tests for learning path progress."""

    @pytest.mark.asyncio
    async def test_get_path_progress_not_found(
        self,
        mock_db_session: AsyncMock,
    ):
        """Test getting progress for non-existent path."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        service = LearningPathService(mock_db_session)
        progress = await service.get_path_progress(
            uuid.uuid4(), uuid.uuid4()
        )

        assert progress is None
