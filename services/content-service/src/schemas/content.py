"""
PANDORA Content Service Content Schemas
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    
    id: UUID
    upload_url: str
    expires_in: int = 3600


class DocumentResponse(BaseModel):
    """Response schema for document."""
    
    id: UUID
    title: str
    description: str | None = None
    content_type: str
    file_size: int
    status: str
    language: str | None = None
    page_count: int | None = None
    word_count: int | None = None
    metadata: dict | None = None
    is_public: bool
    owner_id: UUID | None = None
    license_type: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response schema for paginated document list."""
    
    documents: list[DocumentResponse]
    total: int
    skip: int
    limit: int


class DocumentCreate(BaseModel):
    """Request schema for creating a document record."""
    
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    content_type: str
    file_size: int
    checksum: str | None = None
    language: str | None = None
    license_type: str | None = None
    source_url: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None


class DocumentUpdate(BaseModel):
    """Request schema for updating a document."""
    
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    language: str | None = None
    is_public: bool | None = None
    tags: list[str] | None = None
    metadata: dict | None = None


class CollectionResponse(BaseModel):
    """Response schema for collection."""
    
    id: UUID
    name: str
    description: str | None = None
    is_public: bool
    owner_id: UUID | None = None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CollectionCreate(BaseModel):
    """Request schema for creating a collection."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    is_public: bool = False
    document_ids: list[UUID] | None = None


class CollectionUpdate(BaseModel):
    """Request schema for updating a collection."""
    
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_public: bool | None = None


class CollectionListResponse(BaseModel):
    """Response schema for paginated collection list."""
    
    collections: list[CollectionResponse]
    total: int
    skip: int
    limit: int


class TagResponse(BaseModel):
    """Response schema for tag."""
    
    id: UUID
    name: str
    description: str | None = None
    category: str | None = None
    usage_count: int
    
    class Config:
        from_attributes = True


class UploadUrlRequest(BaseModel):
    """Request for presigned upload URL."""
    
    filename: str
    content_type: str
    file_size: int
    checksum: str | None = None


class DownloadUrlRequest(BaseModel):
    """Request for presigned download URL."""
    
    document_id: UUID
