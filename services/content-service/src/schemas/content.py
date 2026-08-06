"""
PANDORA Content Service Content Schemas
Pydantic models for content management endpoints
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============ Content Schemas ============

class ContentSummary(BaseModel):
    """Summary view of content for listings."""
    
    id: UUID
    title: str
    description: str | None = None
    category: str
    content_type: str
    education_level: str | None = None
    language: str
    status: str
    is_public: bool
    is_featured: bool
    thumbnail_url: str | None = None
    duration_seconds: int | None = None
    page_count: int | None = None
    average_rating: float | None = None
    rating_count: int = 0
    owner_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ContentMetadataSchema(BaseModel):
    """Content metadata schema."""
    
    authors: list[str] | None = None
    author_ids: list[UUID] | None = None
    publication_date: datetime | None = None
    publication_year: int | None = None
    publisher: str | None = None
    isbn: str | None = None
    issn: str | None = None
    doi: str | None = None
    subjects: list[str] | None = None
    keywords: list[str] | None = None
    license_url: str | None = None
    average_rating: float | None = None
    rating_count: int = 0
    view_count: int = 0
    download_count: int = 0
    
    class Config:
        from_attributes = True


class ContentDetail(ContentSummary):
    """Detailed view of content with metadata."""
    
    summary: str | None = None
    content_type: str
    file_size: int | None = None
    storage_key: str | None = None
    checksum: str | None = None
    word_count: int | None = None
    is_premium: bool = False
    license_type: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    extraction_status: str | None = None
    preview_url: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None
    metadata_record: ContentMetadataSchema | None = None
    
    class Config:
        from_attributes = True


class ContentCreate(BaseModel):
    """Request schema for creating content."""
    
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=2000)
    summary: str | None = None
    category: str = Field(..., description="book, article, video, course, lesson, quiz, interactive, document")
    content_type: str = Field(..., description="pdf, epub, mp4, youtube, etc.")
    education_level: str | None = Field(None, description="elementary, middle_school, high_school, undergraduate, graduate, doctoral")
    language: str = Field(default="en", max_length=10)
    
    # File info
    file_size: int | None = None
    storage_key: str | None = None
    checksum: str | None = None
    
    # Media info
    duration_seconds: int | None = None
    page_count: int | None = None
    word_count: int | None = None
    
    # Ownership & Licensing
    license_type: str | None = None
    source_url: str | None = None
    source_name: str | None = None
    
    # Metadata
    tags: list[str] | None = None
    metadata: dict | None = None
    is_public: bool = False
    is_featured: bool = False
    is_premium: bool = False
    
    # Authors & Attribution
    authors: list[str] | None = None
    publication_date: datetime | None = None
    publisher: str | None = None
    isbn: str | None = None
    subjects: list[str] | None = None
    keywords: list[str] | None = None


class ContentUpdate(BaseModel):
    """Request schema for updating content."""
    
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, max_length=2000)
    summary: str | None = None
    education_level: str | None = None
    language: str | None = Field(None, max_length=10)
    
    # Visibility
    is_public: bool | None = None
    is_featured: bool | None = None
    is_premium: bool | None = None
    status: str | None = None
    
    # Metadata
    tags: list[str] | None = None
    metadata: dict | None = None
    
    # Media
    thumbnail_url: str | None = None
    preview_url: str | None = None


class ContentListResponse(BaseModel):
    """Response schema for paginated content list."""
    
    contents: list[ContentSummary]
    total: int
    skip: int
    limit: int
    has_more: bool = False


class RelatedContentResponse(BaseModel):
    """Response schema for related content."""
    
    contents: list[ContentSummary]
    count: int


# ============ Upload/Download Schemas ============

class UploadUrlRequest(BaseModel):
    """Request for presigned upload URL."""
    
    filename: str
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., gt=0, le=104857600)  # Max 100MB
    checksum: str | None = None


class UploadUrlResponse(BaseModel):
    """Response for presigned upload URL."""
    
    upload_url: str
    storage_key: str
    expires_in: int = 3600


class DownloadUrlResponse(BaseModel):
    """Response for presigned download URL."""
    
    download_url: str
    content_type: str
    file_size: int
    expires_in: int = 3600


# ============ Collection Schemas ============

class CollectionResponse(BaseModel):
    """Response schema for collection."""
    
    id: UUID
    name: str
    description: str | None = None
    cover_image_url: str | None = None
    is_public: bool
    is_featured: bool
    owner_id: UUID | None = None
    category: str | None = None
    content_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CollectionCreate(BaseModel):
    """Request schema for creating a collection."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    cover_image_url: str | None = None
    is_public: bool = False
    is_featured: bool = False
    category: str | None = None
    content_ids: list[UUID] | None = None
    metadata: dict | None = None


class CollectionUpdate(BaseModel):
    """Request schema for updating a collection."""
    
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    cover_image_url: str | None = None
    is_public: bool | None = None
    is_featured: bool | None = None
    category: str | None = None
    metadata: dict | None = None


class CollectionListResponse(BaseModel):
    """Response schema for paginated collection list."""
    
    collections: list[CollectionResponse]
    total: int
    skip: int
    limit: int


# ============ Tag Schemas ============

class TagResponse(BaseModel):
    """Response schema for tag."""
    
    id: UUID
    name: str
    slug: str
    description: str | None = None
    category: str | None = None
    usage_count: int = 0
    is_featured: bool = False
    
    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    """Request schema for creating a tag."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    category: str | None = None
    is_featured: bool = False


# ============ Media Asset Schemas ============

class MediaAssetResponse(BaseModel):
    """Response schema for media asset."""
    
    id: UUID
    asset_type: str
    name: str
    description: str | None = None
    url: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    is_primary: bool = False
    order_index: int = 0
    
    class Config:
        from_attributes = True
