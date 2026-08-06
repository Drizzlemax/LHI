"""
PANDORA Content Service Content Routes
API endpoints for content management
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.schemas.content import (
    ContentSummary,
    ContentDetail,
    ContentCreate,
    ContentUpdate,
    ContentListResponse,
    RelatedContentResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    DownloadUrlResponse,
)
from src.services.content_service import ContentService
from src.storage.s3 import get_storage

router = APIRouter(prefix="/content", tags=["Content"])
logger = get_logger(__name__)


@router.get("/", response_model=ContentListResponse)
async def list_content(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    content_type: str | None = None,
    education_level: str | None = None,
    language: str | None = None,
    status: str | None = None,
    is_public: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> ContentListResponse:
    """
    List content with pagination and filters.
    
    Returns a paginated list of content items matching the filter criteria.
    """
    service = ContentService(db)
    contents, total = await service.get_content_list(
        skip=skip,
        limit=limit,
        category=category,
        content_type=content_type,
        education_level=education_level,
        language=language,
        status=status,
        is_public=is_public,
        search=search,
    )
    
    content_summaries = [service._build_content_summary(c) for c in contents]
    
    return ContentListResponse(
        contents=content_summaries,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )


@router.get("/{content_id}", response_model=ContentDetail)
async def get_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ContentDetail:
    """
    Get content details by ID.
    
    Returns full content details including metadata.
    """
    service = ContentService(db)
    content = await service.get_content_detail(content_id)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    return content


@router.get("/{content_id}/related", response_model=RelatedContentResponse)
async def get_related_content(
    content_id: UUID,
    limit: Annotated[int, Query(ge=1, le=20)] = 5,
    db: AsyncSession = Depends(get_db),
) -> RelatedContentResponse:
    """
    Get related content.
    
    Returns content items related to the specified content based on
    category, education level, or subjects.
    """
    service = ContentService(db)
    related = await service.get_related_content(content_id, limit=limit)
    
    return RelatedContentResponse(
        contents=related,
        count=len(related),
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ContentDetail)
async def create_content(
    data: ContentCreate,
    db: AsyncSession = Depends(get_db),
) -> ContentDetail:
    """
    Create new content.
    
    Creates a new content record. Use upload-url to get a presigned
    URL for file uploads, then call this endpoint to create the record.
    """
    service = ContentService(db)
    content = await service.create_content(data)
    
    logger.info("content_created", content_id=str(content.id), title=content.title)
    
    return content


@router.put("/{content_id}", response_model=ContentDetail)
async def update_content(
    content_id: UUID,
    data: ContentUpdate,
    db: AsyncSession = Depends(get_db),
) -> ContentDetail:
    """
    Update content.
    
    Updates the specified content with the provided data.
    """
    service = ContentService(db)
    content = await service.update_content(content_id, data)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    logger.info("content_updated", content_id=str(content_id))
    
    return content


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete content (soft delete).
    
    Performs a soft delete by marking the content as deleted.
    Use restore_content to recover deleted content.
    """
    service = ContentService(db)
    deleted = await service.delete_content(content_id, soft_delete=True)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    logger.info("content_deleted", content_id=str(content_id))


@router.post("/{content_id}/restore", response_model=ContentDetail)
async def restore_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ContentDetail:
    """
    Restore deleted content.
    
    Restores a soft-deleted content back to its previous state.
    """
    service = ContentService(db)
    
    # Update status back to ready
    content = await service.update_content(
        content_id,
        ContentUpdate(status="ready")
    )
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    logger.info("content_restored", content_id=str(content_id))
    
    return content


@router.post("/{content_id}/publish", response_model=ContentDetail)
async def publish_content(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ContentDetail:
    """
    Publish content.
    
    Changes the content status to PUBLISHED, making it visible
    if is_public is set to true.
    """
    service = ContentService(db)
    content = await service.publish_content(content_id)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    logger.info("content_published", content_id=str(content_id))
    
    return content


# ============ Upload/Download Endpoints ============

@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
) -> UploadUrlResponse:
    """
    Get presigned URL for uploading content.
    
    Returns a presigned URL that can be used to upload a file directly
    to S3/MinIO storage.
    """
    storage = get_storage()
    
    # Generate storage key
    import uuid
    doc_id = uuid.uuid4()
    storage_key = storage.generate_storage_key(
        document_id=doc_id,
        content_type=request.content_type,
        original_filename=request.filename,
    )
    
    # Generate presigned upload URL
    try:
        upload_url = storage.generate_upload_url(
            storage_key=storage_key,
            content_type=request.content_type,
            expires_in=3600,
        )
    except Exception as e:
        logger.error("upload_url_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL",
        )
    
    return UploadUrlResponse(
        upload_url=upload_url,
        storage_key=storage_key,
        expires_in=3600,
    )


@router.get("/{content_id}/download", response_model=DownloadUrlResponse)
async def get_download_url(
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> DownloadUrlResponse:
    """
    Get presigned URL for downloading content.
    
    Returns a presigned URL that can be used to download the content file.
    """
    service = ContentService(db)
    content = await service.get_content_by_id(content_id, include_metadata=False)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    if not content.storage_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content has no associated file",
        )
    
    storage = get_storage()
    
    try:
        download_url = storage.generate_download_url(
            storage_key=content.storage_key,
            expires_in=3600,
        )
    except Exception as e:
        logger.error("download_url_failed", content_id=str(content_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL",
        )
    
    return DownloadUrlResponse(
        download_url=download_url,
        content_type=content.content_type,
        file_size=content.file_size or 0,
        expires_in=3600,
    )
