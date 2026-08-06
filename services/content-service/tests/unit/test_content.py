"""
PANDORA Content Service Unit Tests - Content Models
"""
import pytest
from datetime import datetime

pytestmark = pytest.mark.unit


class TestContentCategoryEnum:
    """Tests for ContentCategory enum."""
    
    def test_content_categories(self):
        """Test content category enumeration."""
        from src.models.content import ContentCategory
        assert ContentCategory.BOOK.value == "book"
        assert ContentCategory.ARTICLE.value == "article"
        assert ContentCategory.VIDEO.value == "video"
        assert ContentCategory.COURSE.value == "course"
        assert ContentCategory.LESSON.value == "lesson"
        assert ContentCategory.QUIZ.value == "quiz"
        assert ContentCategory.INTERACTIVE.value == "interactive"
        assert ContentCategory.DOCUMENT.value == "document"


class TestContentTypeEnum:
    """Tests for ContentType enum."""
    
    def test_document_types(self):
        """Test document content types."""
        from src.models.content import ContentType
        assert ContentType.PDF.value == "pdf"
        assert ContentType.EPUB.value == "epub"
        assert ContentType.MARKDOWN.value == "markdown"
    
    def test_video_types(self):
        """Test video content types."""
        from src.models.content import ContentType
        assert ContentType.MP4.value == "mp4"
        assert ContentType.YOUTUBE.value == "youtube"


class TestContentStatusEnum:
    """Tests for ContentStatus enum."""
    
    def test_status_values(self):
        """Test content status enumeration."""
        from src.models.content import ContentStatus
        assert ContentStatus.DRAFT.value == "draft"
        assert ContentStatus.UPLOADED.value == "uploaded"
        assert ContentStatus.PROCESSING.value == "processing"
        assert ContentStatus.READY.value == "ready"
        assert ContentStatus.PUBLISHED.value == "published"
        assert ContentStatus.FAILED.value == "failed"
        assert ContentStatus.ARCHIVED.value == "archived"


class TestEducationLevelEnum:
    """Tests for EducationLevel enum."""
    
    def test_education_levels(self):
        """Test education level enumeration."""
        from src.models.content import EducationLevel
        assert EducationLevel.ELEMENTARY.value == "elementary"
        assert EducationLevel.HIGH_SCHOOL.value == "high_school"
        assert EducationLevel.UNDERGRADUATE.value == "undergraduate"
        assert EducationLevel.DOCTORAL.value == "doctoral"


class TestStorageKey:
    """Tests for storage key generation."""
    
    def test_generate_storage_key(self):
        """Test storage key generation."""
        import uuid
        from src.storage.s3 import LocalStorage
        
        storage = LocalStorage()
        doc_id = uuid.uuid4()
        key = storage.generate_storage_key(
            document_id=doc_id,
            content_type="application/pdf",
            original_filename="test.pdf",
        )
        
        assert str(doc_id) in key
        assert key.endswith(".pdf")
        assert key.startswith("documents/")
    
    def test_checksum_calculation(self):
        """Test checksum calculation."""
        from src.storage.s3 import LocalStorage
        
        storage = LocalStorage()
        checksum = storage.calculate_checksum(b"test data")
        
        assert len(checksum) == 64  # SHA256 hex digest
        assert checksum.isalnum()


class TestContentMetadataModel:
    """Tests for ContentMetadata model structure."""
    
    def test_metadata_fields(self):
        """Test ContentMetadata has expected fields."""
        from src.models.content import ContentMetadata
        fields = ['id', 'content_id', 'authors', 'publication_date', 
                  'license_url', 'average_rating', 'rating_count']
        
        for field in fields:
            assert hasattr(ContentMetadata, field) or field in ContentMetadata.__table__.columns


class TestMediaAssetModel:
    """Tests for MediaAsset model structure."""
    
    def test_media_asset_fields(self):
        """Test MediaAsset has expected fields."""
        from src.models.content import MediaAsset
        fields = ['id', 'content_id', 'asset_type', 'url', 'size', 'mime_type']
        
        for field in fields:
            assert hasattr(MediaAsset, field) or field in MediaAsset.__table__.columns
