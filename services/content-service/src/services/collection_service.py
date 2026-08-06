"""
PANDORA Content Service Collection Business Logic
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.content import Collection, ContentCollection, Content
from src.schemas.content import CollectionCreate, CollectionUpdate, CollectionResponse
from src.core.logging import get_logger

logger = get_logger(__name__)


class CollectionService:
    """Service for collection management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_collection_list(
        self,
        skip: int = 0,
        limit: int = 20,
        is_public: bool | None = None,
        owner_id: uuid.UUID | None = None,
        category: str | None = None,
    ) -> tuple[Sequence[Collection], int]:
        """Get paginated list of collections."""
        query = select(Collection)
        count_query = select(func.count(Collection.id))
        
        filters = []
        if is_public is not None:
            filters.append(Collection.is_public == is_public)
        if owner_id:
            filters.append(Collection.owner_id == owner_id)
        if category:
            filters.append(Collection.category == category)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        query = query.order_by(Collection.created_at.desc()).offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        collections = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        return collections, total
    
    async def get_collection_by_id(
        self,
        collection_id: uuid.UUID,
        include_contents: bool = False,
    ) -> Collection | None:
        """Get collection by ID."""
        query = select(Collection).where(Collection.id == collection_id)
        
        if include_contents:
            query = query.options(
                selectinload(Collection.contents).selectinload(ContentCollection.content)
            )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_collection(
        self,
        data: CollectionCreate,
        owner_id: uuid.UUID | None = None,
    ) -> CollectionResponse:
        """Create a new collection."""
        collection = Collection(
            name=data.name,
            description=data.description,
            cover_image_url=data.cover_image_url,
            is_public=data.is_public,
            is_featured=data.is_featured,
            category=data.category,
            owner_id=owner_id,
            metadata=data.metadata or {},
        )
        
        self.db.add(collection)
        await self.db.flush()
        
        # Add contents if provided
        if data.content_ids:
            for idx, content_id in enumerate(data.content_ids):
                assoc = ContentCollection(
                    collection_id=collection.id,
                    content_id=content_id,
                    order_index=idx,
                )
                self.db.add(assoc)
        
        await self.db.commit()
        await self.db.refresh(collection)
        
        return self._build_response(collection)
    
    async def update_collection(
        self,
        collection_id: uuid.UUID,
        data: CollectionUpdate,
    ) -> CollectionResponse | None:
        """Update a collection."""
        collection = await self.get_collection_by_id(collection_id)
        if not collection:
            return None
        
        if data.name is not None:
            collection.name = data.name
        if data.description is not None:
            collection.description = data.description
        if data.cover_image_url is not None:
            collection.cover_image_url = data.cover_image_url
        if data.is_public is not None:
            collection.is_public = data.is_public
        if data.is_featured is not None:
            collection.is_featured = data.is_featured
        if data.category is not None:
            collection.category = data.category
        if data.metadata is not None:
            collection.metadata = data.metadata
        
        collection.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(collection)
        
        return self._build_response(collection)
    
    async def delete_collection(
        self,
        collection_id: uuid.UUID,
    ) -> bool:
        """Delete a collection."""
        collection = await self.get_collection_by_id(collection_id)
        if not collection:
            return False
        
        await self.db.delete(collection)
        await self.db.commit()
        return True
    
    async def add_content_to_collection(
        self,
        collection_id: uuid.UUID,
        content_id: uuid.UUID,
        order_index: int | None = None,
    ) -> bool:
        """Add content to a collection."""
        # Check if already exists
        query = select(ContentCollection).where(
            and_(
                ContentCollection.collection_id == collection_id,
                ContentCollection.content_id == content_id,
            )
        )
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            return True  # Already exists
        
        assoc = ContentCollection(
            collection_id=collection_id,
            content_id=content_id,
            order_index=order_index or 0,
        )
        self.db.add(assoc)
        await self.db.commit()
        return True
    
    async def remove_content_from_collection(
        self,
        collection_id: uuid.UUID,
        content_id: uuid.UUID,
    ) -> bool:
        """Remove content from a collection."""
        query = select(ContentCollection).where(
            and_(
                ContentCollection.collection_id == collection_id,
                ContentCollection.content_id == content_id,
            )
        )
        result = await self.db.execute(query)
        assoc = result.scalar_one_or_none()
        
        if not assoc:
            return False
        
        await self.db.delete(assoc)
        await self.db.commit()
        return True
    
    def _build_response(self, collection: Collection) -> CollectionResponse:
        """Build CollectionResponse from model."""
        return CollectionResponse(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            cover_image_url=collection.cover_image_url,
            is_public=collection.is_public,
            is_featured=collection.is_featured,
            owner_id=collection.owner_id,
            category=collection.category,
            content_count=len(collection.contents) if hasattr(collection, 'contents') else 0,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )
