"""
PANDORA Content Service Content Business Logic
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.content import (
    Content,
    ContentMetadata,
    ContentStatus,
    ContentCategory,
)
from src.schemas.content import (
    ContentCreate,
    ContentUpdate,
    ContentSummary,
    ContentDetail,
    ContentMetadataSchema,
)
from src.core.logging import get_logger

logger = get_logger(__name__)


class ContentService:
    """Service for content management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_content_list(
        self,
        skip: int = 0,
        limit: int = 20,
        category: str | None = None,
        content_type: str | None = None,
        education_level: str | None = None,
        language: str | None = None,
        status: str | None = None,
        is_public: bool | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[Content], int]:
        """
        Get paginated list of content with filters.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            category: Filter by content category
            content_type: Filter by content type
            education_level: Filter by education level
            language: Filter by language
            status: Filter by status
            is_public: Filter by visibility
            search: Search in title/description
        
        Returns:
            Tuple of (contents, total_count)
        """
        query = select(Content)
        count_query = select(func.count(Content.id))
        
        # Build filters
        filters = []
        
        # Exclude soft-deleted content
        filters.append(Content.deleted_at.is_(None))
        
        if category:
            filters.append(Content.category == category)
        if content_type:
            filters.append(Content.content_type == content_type)
        if education_level:
            filters.append(Content.education_level == education_level)
        if language:
            filters.append(Content.language == language)
        if status:
            filters.append(Content.status == status)
        if is_public is not None:
            filters.append(Content.is_public == is_public)
        if search:
            search_filter = or_(
                Content.title.ilike(f"%{search}%"),
                Content.description.ilike(f"%{search}%"),
            )
            filters.append(search_filter)
        
        # Apply filters
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Order by created_at descending
        query = query.order_by(Content.created_at.desc())
        
        # Pagination
        query = query.offset(skip).limit(limit)
        
        # Execute queries
        result = await self.db.execute(query)
        contents = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        return contents, total
    
    async def get_content_by_id(
        self,
        content_id: uuid.UUID,
        include_metadata: bool = True,
    ) -> Content | None:
        """
        Get content by ID.
        
        Args:
            content_id: Content UUID
            include_metadata: Whether to load metadata relationship
        
        Returns:
            Content if found, None otherwise
        """
        query = select(Content).where(Content.id == content_id)
        
        if include_metadata:
            query = query.options(selectinload(Content.metadata_record))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_content_detail(
        self,
        content_id: uuid.UUID,
    ) -> ContentDetail | None:
        """
        Get detailed content information.
        
        Args:
            content_id: Content UUID
        
        Returns:
            ContentDetail if found, None otherwise
        """
        content = await self.get_content_by_id(content_id, include_metadata=True)
        
        if not content:
            return None
        
        # Increment view count
        if content.metadata_record:
            content.metadata_record.view_count += 1
            await self.db.commit()
        
        # Build response
        return self._build_content_detail(content)
    
    async def get_related_content(
        self,
        content_id: uuid.UUID,
        limit: int = 5,
    ) -> list[ContentSummary]:
        """
        Get related content based on same category/subjects.
        
        Args:
            content_id: Source content UUID
            limit: Maximum number of related items
        
        Returns:
            List of related ContentSummary
        """
        # Get source content
        source = await self.get_content_by_id(content_id, include_metadata=False)
        if not source:
            return []
        
        # Find related content
        query = (
            select(Content)
            .where(
                and_(
                    Content.id != content_id,
                    Content.deleted_at.is_(None),
                    Content.status.in_([ContentStatus.READY.value, ContentStatus.PUBLISHED.value]),
                    or_(
                        Content.category == source.category,
                        Content.education_level == source.education_level,
                    )
                )
            )
            .options(selectinload(Content.metadata_record))
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        contents = result.scalars().all()
        
        return [self._build_content_summary(c) for c in contents]
    
    async def create_content(
        self,
        data: ContentCreate,
        owner_id: uuid.UUID | None = None,
    ) -> ContentDetail:
        """
        Create new content.
        
        Args:
            data: Content creation data
            owner_id: Owner user ID
        
        Returns:
            Created ContentDetail
        """
        # Create content record
        content = Content(
            title=data.title,
            description=data.description,
            summary=data.summary,
            category=data.category,
            content_type=data.content_type,
            education_level=data.education_level,
            language=data.language,
            file_size=data.file_size,
            storage_key=data.storage_key,
            checksum=data.checksum,
            duration_seconds=data.duration_seconds,
            page_count=data.page_count,
            word_count=data.word_count,
            status=ContentStatus.DRAFT.value,
            license_type=data.license_type,
            source_url=data.source_url,
            source_name=data.source_name,
            tags=data.tags,
            metadata=data.metadata or {},
            is_public=data.is_public,
            is_featured=data.is_featured,
            is_premium=data.is_premium,
            owner_id=owner_id,
            creator_id=owner_id,
        )
        
        self.db.add(content)
        await self.db.flush()
        
        # Create metadata record
        if data.authors or data.publication_date or data.publisher:
            metadata = ContentMetadata(
                content_id=content.id,
                authors=data.authors,
                publication_date=data.publication_date,
                publisher=data.publisher,
                isbn=data.isbn,
                subjects=data.subjects,
                keywords=data.keywords,
            )
            self.db.add(metadata)
            await self.db.flush()
            content.metadata_record = metadata
        
        await self.db.commit()
        await self.db.refresh(content)
        
        return self._build_content_detail(content)
    
    async def update_content(
        self,
        content_id: uuid.UUID,
        data: ContentUpdate,
    ) -> ContentDetail | None:
        """
        Update existing content.
        
        Args:
            content_id: Content UUID
            data: Update data
        
        Returns:
            Updated ContentDetail if found, None otherwise
        """
        content = await self.get_content_by_id(content_id, include_metadata=True)
        if not content:
            return None
        
        # Update fields
        if data.title is not None:
            content.title = data.title
        if data.description is not None:
            content.description = data.description
        if data.summary is not None:
            content.summary = data.summary
        if data.education_level is not None:
            content.education_level = data.education_level
        if data.language is not None:
            content.language = data.language
        if data.is_public is not None:
            content.is_public = data.is_public
        if data.is_featured is not None:
            content.is_featured = data.is_featured
        if data.is_premium is not None:
            content.is_premium = data.is_premium
        if data.status is not None:
            content.status = data.status
        if data.tags is not None:
            content.tags = data.tags
        if data.metadata is not None:
            content.metadata = data.metadata
        if data.thumbnail_url is not None:
            content.thumbnail_url = data.thumbnail_url
        if data.preview_url is not None:
            content.preview_url = data.preview_url
        
        content.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(content)
        
        return self._build_content_detail(content)
    
    async def delete_content(
        self,
        content_id: uuid.UUID,
        soft_delete: bool = True,
    ) -> bool:
        """
        Delete content.
        
        Args:
            content_id: Content UUID
            soft_delete: If True, mark as deleted; if False, permanently delete
        
        Returns:
            True if deleted, False if not found
        """
        content = await self.get_content_by_id(content_id, include_metadata=False)
        if not content:
            return False
        
        if soft_delete:
            content.deleted_at = datetime.now(timezone.utc)
            content.status = ContentStatus.DELETED.value
        else:
            await self.db.delete(content)
        
        await self.db.commit()
        return True
    
    async def publish_content(
        self,
        content_id: uuid.UUID,
    ) -> ContentDetail | None:
        """
        Publish content (change status to PUBLISHED).
        
        Args:
            content_id: Content UUID
        
        Returns:
            Updated ContentDetail if found
        """
        return await self.update_content(
            content_id,
            ContentUpdate(status=ContentStatus.PUBLISHED.value)
        )
    
    def _build_content_summary(self, content: Content) -> ContentSummary:
        """Build ContentSummary from Content model."""
        rating = None
        rating_count = 0
        if content.metadata_record:
            rating = content.metadata_record.average_rating
            rating_count = content.metadata_record.rating_count
        
        return ContentSummary(
            id=content.id,
            title=content.title,
            description=content.description,
            category=content.category,
            content_type=content.content_type,
            education_level=content.education_level,
            language=content.language,
            status=content.status,
            is_public=content.is_public,
            is_featured=content.is_featured,
            thumbnail_url=content.thumbnail_url,
            duration_seconds=content.duration_seconds,
            page_count=content.page_count,
            average_rating=rating,
            rating_count=rating_count,
            owner_id=content.owner_id,
            created_at=content.created_at,
            updated_at=content.updated_at,
        )
    
    def _build_content_detail(self, content: Content) -> ContentDetail:
        """Build ContentDetail from Content model."""
        metadata_schema = None
        if content.metadata_record:
            metadata_schema = ContentMetadataSchema(
                authors=content.metadata_record.authors,
                author_ids=content.metadata_record.author_ids,
                publication_date=content.metadata_record.publication_date,
                publication_year=content.metadata_record.publication_year,
                publisher=content.metadata_record.publisher,
                isbn=content.metadata_record.isbn,
                issn=content.metadata_record.issn,
                doi=content.metadata_record.doi,
                subjects=content.metadata_record.subjects,
                keywords=content.metadata_record.keywords,
                license_url=content.metadata_record.license_url,
                average_rating=content.metadata_record.average_rating,
                rating_count=content.metadata_record.rating_count,
                view_count=content.metadata_record.view_count,
                download_count=content.metadata_record.download_count,
            )
        
        return ContentDetail(
            id=content.id,
            title=content.title,
            description=content.description,
            summary=content.summary,
            category=content.category,
            content_type=content.content_type,
            education_level=content.education_level,
            language=content.language,
            status=content.status,
            is_public=content.is_public,
            is_featured=content.is_featured,
            thumbnail_url=content.thumbnail_url,
            duration_seconds=content.duration_seconds,
            page_count=content.page_count,
            average_rating=metadata_schema.average_rating if metadata_schema else None,
            rating_count=metadata_schema.rating_count if metadata_schema else 0,
            owner_id=content.owner_id,
            created_at=content.created_at,
            updated_at=content.updated_at,
            # Detail fields
            file_size=content.file_size,
            storage_key=content.storage_key,
            checksum=content.checksum,
            word_count=content.word_count,
            is_premium=content.is_premium,
            license_type=content.license_type,
            source_url=content.source_url,
            source_name=content.source_name,
            extraction_status=content.extraction_status,
            preview_url=content.preview_url,
            tags=content.tags,
            metadata=content.metadata,
            metadata_record=metadata_schema,
        )
