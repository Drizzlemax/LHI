"""
PANDORA Content Service S3 Storage Module
"""
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class S3Storage:
    """S3 storage handler for document files."""
    
    def __init__(self):
        """Initialize S3 client."""
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
            region_name=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
        )
        self.bucket_name = settings.s3_bucket_name
    
    def generate_storage_key(
        self,
        document_id: uuid.UUID,
        content_type: str,
        original_filename: str,
    ) -> str:
        """Generate a unique storage key for a document."""
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        extension = self._get_extension(original_filename, content_type)
        return f"documents/{date_prefix}/{document_id}/{document_id}{extension}"
    
    def _get_extension(self, filename: str, content_type: str) -> str:
        """Get file extension from filename or content type."""
        if "." in filename:
            return filename.rsplit(".", 1)[1].lower()
        
        # Map content types to extensions
        extension_map = {
            "application/pdf": ".pdf",
            "application/epub+zip": ".epub",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "text/plain": ".txt",
            "text/html": ".html",
            "text/markdown": ".md",
        }
        return extension_map.get(content_type, ".bin")
    
    def calculate_checksum(self, file_data: bytes) -> str:
        """Calculate SHA256 checksum of file data."""
        return hashlib.sha256(file_data).hexdigest()
    
    async def upload_file(
        self,
        file_data: bytes,
        storage_key: str,
        content_type: str,
    ) -> bool:
        """Upload a file to S3."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=storage_key,
                Body=file_data,
                ContentType=content_type,
            )
            logger.info("file_uploaded", storage_key=storage_key)
            return True
        except ClientError as e:
            logger.error("upload_failed", storage_key=storage_key, error=str(e))
            return False
    
    async def upload_file_obj(
        self,
        file_obj: BinaryIO,
        storage_key: str,
        content_type: str,
    ) -> bool:
        """Upload a file object to S3."""
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                storage_key,
                ExtraArgs={"ContentType": content_type},
            )
            logger.info("file_uploaded", storage_key=storage_key)
            return True
        except ClientError as e:
            logger.error("upload_failed", storage_key=storage_key, error=str(e))
            return False
    
    def generate_upload_url(
        self,
        storage_key: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for uploading."""
        try:
            url = self.s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": storage_key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error("presign_failed", storage_key=storage_key, error=str(e))
            raise
    
    def generate_download_url(
        self,
        storage_key: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for downloading."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": storage_key,
                },
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error("presign_failed", storage_key=storage_key, error=str(e))
            raise
    
    async def delete_file(self, storage_key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )
            logger.info("file_deleted", storage_key=storage_key)
            return True
        except ClientError as e:
            logger.error("delete_failed", storage_key=storage_key, error=str(e))
            return False
    
    async def file_exists(self, storage_key: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )
            return True
        except ClientError:
            return False
    
    async def get_file_size(self, storage_key: str) -> int | None:
        """Get the size of a file in S3."""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_key,
            )
            return response.get("ContentLength")
        except ClientError:
            return None


class LocalStorage:
    """Local filesystem storage handler (for development/testing)."""
    
    def __init__(self):
        """Initialize local storage."""
        import os
        self.storage_path = settings.local_storage_path
        os.makedirs(self.storage_path, exist_ok=True)
    
    def generate_storage_key(
        self,
        document_id: uuid.UUID,
        content_type: str,
        original_filename: str,
    ) -> str:
        """Generate a unique storage key for a document."""
        date_prefix = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        extension = self._get_extension(original_filename, content_type)
        return f"documents/{date_prefix}/{document_id}/{document_id}{extension}"
    
    def _get_extension(self, filename: str, content_type: str) -> str:
        """Get file extension from filename or content type."""
        if "." in filename:
            return filename.rsplit(".", 1)[1].lower()
        
        extension_map = {
            "application/pdf": ".pdf",
            "application/epub+zip": ".epub",
            "application/msword": ".doc",
            "text/plain": ".txt",
        }
        return extension_map.get(content_type, ".bin")
    
    def calculate_checksum(self, file_data: bytes) -> str:
        """Calculate SHA256 checksum of file data."""
        return hashlib.sha256(file_data).hexdigest()
    
    async def upload_file(
        self,
        file_data: bytes,
        storage_key: str,
        content_type: str,
    ) -> bool:
        """Upload a file to local storage."""
        import os
        import aiofiles
        
        full_path = os.path.join(self.storage_path, storage_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_data)
        
        logger.info("file_uploaded", storage_key=storage_key)
        return True
    
    async def delete_file(self, storage_key: str) -> bool:
        """Delete a file from local storage."""
        import os
        
        full_path = os.path.join(self.storage_path, storage_key)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info("file_deleted", storage_key=storage_key)
            return True
        return False


def get_storage() -> S3Storage | LocalStorage:
    """Get the appropriate storage handler based on configuration."""
    if settings.storage_backend == "local":
        return LocalStorage()
    return S3Storage()
