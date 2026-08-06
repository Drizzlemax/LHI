"""
PANDORA Content Service Unit Tests - Content
"""
import pytest

pytestmark = pytest.mark.unit


class TestDocumentModel:
    """Tests for Document model."""
    
    def test_content_type_enum(self):
        """Test content type enumeration."""
        from src.models.content import ContentType
        assert ContentType.PDF.value == "pdf"
        assert ContentType.EPUB.value == "epub"
    
    def test_content_status_enum(self):
        """Test content status enumeration."""
        from src.models.content import ContentStatus
        assert ContentStatus.UPLOADED.value == "uploaded"
        assert ContentStatus.PROCESSING.value == "processing"
        assert ContentStatus.READY.value == "ready"


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
