"""
PANDORA Content Service Unit Tests - Storage
"""
import hashlib
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from src.storage.s3 import S3Storage, LocalStorage, get_storage


pytestmark = pytest.mark.unit


class TestLocalStorage:
    """Tests for LocalStorage."""
    
    @pytest.fixture
    def storage(self) -> LocalStorage:
        """Create LocalStorage instance."""
        with patch("src.storage.s3.settings") as mock_settings:
            mock_settings.local_storage_path = "/tmp/test_storage"
            return LocalStorage()
    
    def test_generate_storage_key_pdf(self, storage: LocalStorage):
        """Test storage key generation for PDF."""
        doc_id = uuid.uuid4()
        key = storage.generate_storage_key(
            document_id=doc_id,
            content_type="application/pdf",
            original_filename="test.pdf",
        )
        
        assert str(doc_id) in key
        assert key.endswith(".pdf")
        assert key.startswith("documents/")
    
    def test_generate_storage_key_epub(self, storage: LocalStorage):
        """Test storage key generation for EPUB."""
        doc_id = uuid.uuid4()
        key = storage.generate_storage_key(
            document_id=doc_id,
            content_type="application/epub+zip",
            original_filename="book",
        )
        
        assert str(doc_id) in key
        assert key.endswith(".epub")
    
    def test_generate_storage_key_by_content_type(self, storage: LocalStorage):
        """Test storage key generation by content type."""
        doc_id = uuid.uuid4()
        key = storage.generate_storage_key(
            document_id=doc_id,
            content_type="text/plain",
            original_filename="noextension",
        )
        
        assert key.endswith(".txt")
    
    def test_calculate_checksum(self, storage: LocalStorage):
        """Test checksum calculation."""
        data = b"Hello, World!"
        checksum = storage.calculate_checksum(data)
        
        # Verify it's SHA256
        expected = hashlib.sha256(data).hexdigest()
        assert checksum == expected
        assert len(checksum) == 64
    
    def test_calculate_checksum_empty(self, storage: LocalStorage):
        """Test checksum of empty data."""
        checksum = storage.calculate_checksum(b"")
        
        assert len(checksum) == 64
        assert checksum.isalnum()
    
    def test_get_extension_from_filename(self, storage: LocalStorage):
        """Test extension extraction from filename."""
        ext = storage._get_extension("document.pdf", "application/pdf")
        assert ext == ".pdf"
        
        ext = storage._get_extension("book.epub", "application/epub+zip")
        assert ext == ".epub"
    
    def test_get_extension_from_content_type(self, storage: LocalStorage):
        """Test extension extraction from content type."""
        ext = storage._get_extension("noextension", "text/markdown")
        assert ext == ".md"
        
        ext = storage._get_extension("noextension", "text/html")
        assert ext == ".html"
    
    def test_get_extension_unknown_type(self, storage: LocalStorage):
        """Test extension for unknown content type."""
        ext = storage._get_extension("file", "application/unknown")
        assert ext == ".bin"


class TestS3Storage:
    """Tests for S3Storage."""
    
    @pytest.fixture
    def storage(self) -> S3Storage:
        """Create S3Storage with mocked boto3 client."""
        with patch("src.storage.s3.boto3") as mock_boto3:
            mock_client = MagicMock()
            mock_boto3.client.return_value = mock_client
            
            with patch("src.storage.s3.settings") as mock_settings:
                mock_settings.aws_access_key_id = "test_key"
                mock_settings.aws_secret_access_key = "test_secret"
                mock_settings.aws_region = "us-east-1"
                mock_settings.s3_bucket_name = "test-bucket"
                mock_settings.s3_endpoint_url = None
                
                storage = S3Storage()
                return storage
    
    def test_generate_storage_key(self, storage: S3Storage):
        """Test storage key generation."""
        doc_id = uuid.uuid4()
        key = storage.generate_storage_key(
            document_id=doc_id,
            content_type="application/pdf",
            original_filename="document.pdf",
        )
        
        assert str(doc_id) in key
        assert key.endswith(".pdf")
        assert key.startswith("documents/")
    
    def test_calculate_checksum(self, storage: S3Storage):
        """Test checksum calculation."""
        data = b"Test content"
        checksum = storage.calculate_checksum(data)
        
        expected = hashlib.sha256(data).hexdigest()
        assert checksum == expected
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage: S3Storage):
        """Test successful file upload."""
        storage.s3_client.put_object = MagicMock()
        
        result = await storage.upload_file(
            file_data=b"test content",
            storage_key="documents/test/file.pdf",
            content_type="application/pdf",
        )
        
        assert result is True
        storage.s3_client.put_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_failure(self, storage: S3Storage):
        """Test failed file upload."""
        from botocore.exceptions import ClientError
        
        storage.s3_client.put_object = MagicMock(
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal error"}},
                "PutObject"
            )
        )
        
        result = await storage.upload_file(
            file_data=b"test content",
            storage_key="documents/test/file.pdf",
            content_type="application/pdf",
        )
        
        assert result is False
    
    def test_generate_upload_url(self, storage: S3Storage):
        """Test presigned upload URL generation."""
        storage.s3_client.generate_presigned_url = MagicMock(
            return_value="https://s3.example.com/presigned-upload"
        )
        
        url = storage.generate_upload_url(
            storage_key="documents/test/file.pdf",
            content_type="application/pdf",
            expires_in=3600,
        )
        
        assert url == "https://s3.example.com/presigned-upload"
        storage.s3_client.generate_presigned_url.assert_called_once()
    
    def test_generate_download_url(self, storage: S3Storage):
        """Test presigned download URL generation."""
        storage.s3_client.generate_presigned_url = MagicMock(
            return_value="https://s3.example.com/presigned-download"
        )
        
        url = storage.generate_download_url(
            storage_key="documents/test/file.pdf",
            expires_in=3600,
        )
        
        assert url == "https://s3.example.com/presigned-download"
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage: S3Storage):
        """Test successful file deletion."""
        storage.s3_client.delete_object = MagicMock()
        
        result = await storage.delete_file("documents/test/file.pdf")
        
        assert result is True
        storage.s3_client.delete_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file_failure(self, storage: S3Storage):
        """Test failed file deletion."""
        from botocore.exceptions import ClientError
        
        storage.s3_client.delete_object = MagicMock(
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal error"}},
                "DeleteObject"
            )
        )
        
        result = await storage.delete_file("documents/test/file.pdf")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_file_exists_true(self, storage: S3Storage):
        """Test file exists check - file found."""
        storage.s3_client.head_object = MagicMock()
        
        result = await storage.file_exists("documents/test/file.pdf")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_file_exists_false(self, storage: S3Storage):
        """Test file exists check - file not found."""
        from botocore.exceptions import ClientError
        
        storage.s3_client.head_object = MagicMock(
            side_effect=ClientError(
                {"Error": {"Code": "404", "Message": "Not found"}},
                "HeadObject"
            )
        )
        
        result = await storage.file_exists("documents/test/file.pdf")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_file_size(self, storage: S3Storage):
        """Test getting file size."""
        storage.s3_client.head_object = MagicMock(
            return_value={"ContentLength": 1024000}
        )
        
        size = await storage.get_file_size("documents/test/file.pdf")
        
        assert size == 1024000
    
    @pytest.mark.asyncio
    async def test_get_file_size_not_found(self, storage: S3Storage):
        """Test getting file size for non-existent file."""
        from botocore.exceptions import ClientError
        
        storage.s3_client.head_object = MagicMock(
            side_effect=ClientError(
                {"Error": {"Code": "404", "Message": "Not found"}},
                "HeadObject"
            )
        )
        
        size = await storage.get_file_size("documents/test/file.pdf")
        
        assert size is None


class TestGetStorage:
    """Tests for get_storage factory function."""
    
    def test_get_storage_local(self):
        """Test getting local storage."""
        with patch("src.storage.s3.settings") as mock_settings:
            mock_settings.storage_backend = "local"
            mock_settings.local_storage_path = "/tmp/test"
            
            storage = get_storage()
            
            assert isinstance(storage, LocalStorage)
    
    def test_get_storage_s3(self):
        """Test getting S3 storage."""
        with patch("src.storage.s3.settings") as mock_settings:
            mock_settings.storage_backend = "s3"
            mock_settings.aws_access_key_id = "test"
            mock_settings.aws_secret_access_key = "test"
            mock_settings.aws_region = "us-east-1"
            mock_settings.s3_bucket_name = "test"
            mock_settings.s3_endpoint_url = None
            
            with patch("src.storage.s3.boto3"):
                storage = get_storage()
                
                assert isinstance(storage, S3Storage)


class TestStorageIntegration:
    """Integration tests for storage (require actual storage backend)."""
    
    @pytest.fixture
    def integration_storage(self):
        """Storage for integration tests."""
        # These tests would require actual S3 or local storage
        # Skip if not configured
        pytest.skip("Integration tests require storage backend")
    
    @pytest.mark.asyncio
    async def test_full_upload_download_cycle(self, integration_storage):
        """Test complete upload and download cycle."""
        pass
