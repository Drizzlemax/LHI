"""
PANDORA Content Service Unit Tests - Content Service
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.content import (
    Content,
    ContentMetadata,
    ContentStatus,
    ContentCategory,
)
from src.schemas.content import (
    ContentCreate,
    ContentUpdate,
)
from src.services.content_service import ContentService


pytestmark = pytest.mark.unit


class TestContentService:
    """Tests for ContentService."""
    
    @pytest.fixture
    def service(self, mock_db_session: AsyncMock) -> ContentService:
        """Create ContentService instance with mock session."""
        return ContentService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_get_content_list_empty(self, service: ContentService):
        """Test getting empty content list."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        service.db.execute = AsyncMock(
            side_effect=[mock_result, mock_count_result]
        )
        
        contents, total = await service.get_content_list()
        
        assert contents == []
        assert total == 0
    
    @pytest.mark.asyncio
    async def test_get_content_list_with_filters(self, service: ContentService):
        """Test getting content list with filters."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        
        service.db.execute = AsyncMock(
            side_effect=[mock_result, mock_count_result]
        )
        
        contents, total = await service.get_content_list(
            category=ContentCategory.COURSE.value,
            language="en",
            status=ContentStatus.PUBLISHED.value,
            is_public=True,
            search="machine",
        )
        
        assert total == 0
        service.db.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_content_by_id_not_found(self, service: ContentService):
        """Test getting non-existent content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        service.db.execute = AsyncMock(return_value=mock_result)
        
        content = await service.get_content_by_id(uuid.uuid4())
        
        assert content is None
    
    @pytest.mark.asyncio
    async def test_get_content_by_id_found(self, service: ContentService, sample_content: Content):
        """Test getting existing content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        
        service.db.execute = AsyncMock(return_value=mock_result)
        
        content = await service.get_content_by_id(sample_content.id)
        
        assert content is not None
        assert content.id == sample_content.id
        assert content.title == sample_content.title
    
    @pytest.mark.asyncio
    async def test_create_content_basic(self, service: ContentService):
        """Test creating basic content."""
        data = ContentCreate(
            title="Test Content",
            description="Test description",
            category=ContentCategory.DOCUMENT.value,
            content_type="pdf",
        )
        
        # Mock the flush and refresh
        service.db.flush = AsyncMock()
        service.db.refresh = AsyncMock()
        service.db.commit = AsyncMock()
        
        result = await service.create_content(data)
        
        assert result.title == "Test Content"
        assert result.category == ContentCategory.DOCUMENT.value
        service.db.add.assert_called_once()
        service.db.flush.assert_called()
        service.db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_content_with_metadata(self, service: ContentService):
        """Test creating content with metadata."""
        data = ContentCreate(
            title="Test Book",
            description="A test book",
            category=ContentCategory.BOOK.value,
            content_type="epub",
            authors=["John Doe", "Jane Smith"],
            publication_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            publisher="Test Publisher",
        )
        
        service.db.flush = AsyncMock()
        service.db.refresh = AsyncMock()
        service.db.commit = AsyncMock()
        
        result = await service.create_content(data)
        
        assert result.title == "Test Book"
        assert result.metadata_record is not None
    
    @pytest.mark.asyncio
    async def test_update_content_not_found(self, service: ContentService):
        """Test updating non-existent content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        service.db.execute = AsyncMock(return_value=mock_result)
        
        data = ContentUpdate(title="Updated Title")
        result = await service.update_content(uuid.uuid4(), data)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_content_success(self, service: ContentService, sample_content: Content):
        """Test updating existing content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        
        service.db.execute = AsyncMock(return_value=mock_result)
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()
        
        data = ContentUpdate(
            title="Updated Title",
            description="Updated description",
            is_public=True,
        )
        
        result = await service.update_content(sample_content.id, data)
        
        assert result is not None
        assert sample_content.title == "Updated Title"
        service.db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_content_not_found(self, service: ContentService):
        """Test deleting non-existent content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        service.db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.delete_content(uuid.uuid4())
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_content_soft_delete(self, service: ContentService, sample_content: Content):
        """Test soft deleting content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        
        service.db.execute = AsyncMock(return_value=mock_result)
        service.db.commit = AsyncMock()
        
        result = await service.delete_content(sample_content.id, soft_delete=True)
        
        assert result is True
        assert sample_content.deleted_at is not None
        assert sample_content.status == ContentStatus.DELETED.value
        service.db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_content_hard_delete(self, service: ContentService, sample_content: Content):
        """Test hard deleting content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        
        service.db.execute = AsyncMock(return_value=mock_result)
        service.db.delete = AsyncMock()
        service.db.commit = AsyncMock()
        
        result = await service.delete_content(sample_content.id, soft_delete=False)
        
        assert result is True
        service.db.delete.assert_called_with(sample_content)
    
    @pytest.mark.asyncio
    async def test_publish_content(self, service: ContentService, sample_content: Content):
        """Test publishing content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_content
        
        service.db.execute = AsyncMock(return_value=mock_result)
        service.db.commit = AsyncMock()
        service.db.refresh = AsyncMock()
        
        result = await service.publish_content(sample_content.id)
        
        assert result is not None
        assert sample_content.status == ContentStatus.PUBLISHED.value
    
    @pytest.mark.asyncio
    async def test_get_related_content_not_found(self, service: ContentService):
        """Test getting related content for non-existent content."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        service.db.execute = AsyncMock(return_value=mock_result)
        
        result = await service.get_related_content(uuid.uuid4())
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_related_content_found(self, service: ContentService, sample_content: Content):
        """Test getting related content."""
        # First call returns source content
        mock_source_result = MagicMock()
        mock_source_result.scalar_one_or_none.return_value = sample_content
        
        # Second call returns related content
        mock_related_result = MagicMock()
        mock_related_result.scalars.return_value.all.return_value = []
        
        service.db.execute = AsyncMock(
            side_effect=[mock_source_result, mock_related_result]
        )
        
        result = await service.get_related_content(sample_content.id)
        
        assert isinstance(result, list)
    
    def test_build_content_summary(self, service: ContentService, sample_content: Content):
        """Test building content summary."""
        sample_content.metadata_record = None
        
        summary = service._build_content_summary(sample_content)
        
        assert summary.id == sample_content.id
        assert summary.title == sample_content.title
        assert summary.category == sample_content.category
        assert summary.average_rating is None
        assert summary.rating_count == 0
    
    def test_build_content_summary_with_metadata(
        self, service: ContentService, sample_content: Content, sample_content_metadata: ContentMetadata
    ):
        """Test building content summary with metadata."""
        sample_content.metadata_record = sample_content_metadata
        
        summary = service._build_content_summary(sample_content)
        
        assert summary.average_rating == 4.5
        assert summary.rating_count == 128
    
    def test_build_content_detail(
        self, service: ContentService, sample_content: Content, sample_content_metadata: ContentMetadata
    ):
        """Test building content detail."""
        sample_content.metadata_record = sample_content_metadata
        
        detail = service._build_content_detail(sample_content)
        
        assert detail.id == sample_content.id
        assert detail.title == sample_content.title
        assert detail.metadata_record is not None
        assert detail.metadata_record.authors == ["John Doe", "Jane Smith"]
        assert detail.metadata_record.average_rating == 4.5


class TestContentServicePagination:
    """Tests for ContentService pagination."""
    
    @pytest.fixture
    def service(self, mock_db_session: AsyncMock) -> ContentService:
        return ContentService(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_pagination_skip_limit(self, service: ContentService):
        """Test pagination with skip and limit."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50
        
        service.db.execute = AsyncMock(
            side_effect=[mock_result, mock_count_result]
        )
        
        contents, total = await service.get_content_list(skip=10, limit=20)
        
        assert total == 50
    
    @pytest.mark.asyncio
    async def test_has_more_calculation(self, service: ContentService, async_client):
        """Test has_more calculation in response."""
        # This tests the API response format
        pass  # API-level test


class TestContentEnums:
    """Tests for content enums."""
    
    def test_content_category_values(self):
        """Test ContentCategory enum values."""
        assert ContentCategory.BOOK.value == "book"
        assert ContentCategory.ARTICLE.value == "article"
        assert ContentCategory.VIDEO.value == "video"
        assert ContentCategory.COURSE.value == "course"
        assert ContentCategory.LESSON.value == "lesson"
        assert ContentCategory.QUIZ.value == "quiz"
        assert ContentCategory.INTERACTIVE.value == "interactive"
        assert ContentCategory.DOCUMENT.value == "document"
    
    def test_content_status_values(self):
        """Test ContentStatus enum values."""
        assert ContentStatus.DRAFT.value == "draft"
        assert ContentStatus.UPLOADED.value == "uploaded"
        assert ContentStatus.PROCESSING.value == "processing"
        assert ContentStatus.READY.value == "ready"
        assert ContentStatus.PUBLISHED.value == "published"
        assert ContentStatus.FAILED.value == "failed"
        assert ContentStatus.ARCHIVED.value == "archived"
        assert ContentStatus.DELETED.value == "deleted"
