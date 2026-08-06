"""
PANDORA Content Service Collections Routes
API endpoints for collection management
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import get_logger
from src.schemas.content import (
    CollectionResponse,
    CollectionListResponse,
    CollectionCreate,
    CollectionUpdate,
)
from src.services.collection_service import CollectionService

router = APIRouter(prefix="/collections", tags=["Collections"])
logger = get_logger(__name__)


@router.get("/", response_model=CollectionListResponse)
async def list_collections(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    is_public: bool | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> CollectionListResponse:
    """
    List collections with pagination.
    
    Returns a paginated list of collections.
    """
    service = CollectionService(db)
    collections, total = await service.get_collection_list(
        skip=skip,
        limit=limit,
        is_public=is_public,
        category=category,
    )
    
    return CollectionListResponse(
        collections=[service._build_response(c) for c in collections],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=CollectionResponse)
async def create_collection(
    data: CollectionCreate,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """
    Create a new collection.
    
    Collections are used to organize and group related content.
    """
    service = CollectionService(db)
    collection = await service.create_collection(data)
    
    logger.info("collection_created", collection_id=str(collection.id), name=collection.name)
    
    return collection


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Get collection by ID."""
    service = CollectionService(db)
    collection = await service.get_collection_by_id(collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    
    return service._build_response(collection)


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: UUID,
    data: CollectionUpdate,
    db: AsyncSession = Depends(get_db),
) -> CollectionResponse:
    """Update collection metadata."""
    service = CollectionService(db)
    collection = await service.update_collection(collection_id, data)
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    
    logger.info("collection_updated", collection_id=str(collection_id))
    
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a collection."""
    service = CollectionService(db)
    deleted = await service.delete_collection(collection_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    
    logger.info("collection_deleted", collection_id=str(collection_id))


@router.post("/{collection_id}/contents/{content_id}", status_code=status.HTTP_201_CREATED)
async def add_content_to_collection(
    collection_id: UUID,
    content_id: UUID,
    order_index: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add content to a collection."""
    service = CollectionService(db)
    
    # Verify collection exists
    collection = await service.get_collection_by_id(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )
    
    await service.add_content_to_collection(collection_id, content_id, order_index)
    
    return {"message": "Content added to collection"}


@router.delete("/{collection_id}/contents/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_content_from_collection(
    collection_id: UUID,
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove content from a collection."""
    service = CollectionService(db)
    removed = await service.remove_content_from_collection(collection_id, content_id)
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found in collection",
        )
