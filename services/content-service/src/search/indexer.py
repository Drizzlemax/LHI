"""
PANDORA Content Service Elasticsearch Indexer
Index creation, mappings, and bulk indexing for content
"""
import uuid
from datetime import datetime
from typing import Any

from src.search.client import ElasticsearchClient, get_es_client
from src.core.logging import get_logger

logger = get_logger(__name__)


# Index name
CONTENT_INDEX = "pandora_content"


# Index settings for optimization
INDEX_SETTINGS = {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "analysis": {
        "analyzer": {
            "autocomplete_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "autocomplete_filter",
                ],
            },
            "autocomplete_search_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                ],
            },
            "text_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "asciifolding",
                    "porter_stem",
                ],
            },
        },
        "filter": {
            "autocomplete_filter": {
                "type": "edge_ngram",
                "min_gram": 2,
                "max_gram": 20,
            },
        },
    },
}


# Content index mappings
CONTENT_MAPPINGS = {
    "properties": {
        # Basic Info
        "id": {"type": "keyword"},
        "title": {
            "type": "text",
            "analyzer": "text_analyzer",
            "fields": {
                "keyword": {"type": "keyword"},
                "autocomplete": {
                    "type": "text",
                    "analyzer": "autocomplete_analyzer",
                    "search_analyzer": "autocomplete_search_analyzer",
                },
            },
        },
        "description": {
            "type": "text",
            "analyzer": "text_analyzer",
        },
        "summary": {
            "type": "text",
            "analyzer": "text_analyzer",
        },
        
        # Classification
        "category": {"type": "keyword"},
        "content_type": {"type": "keyword"},
        "education_level": {"type": "keyword"},
        
        # Language & Region
        "language": {"type": "keyword"},
        
        # Content Details
        "is_public": {"type": "boolean"},
        "is_featured": {"type": "boolean"},
        "is_premium": {"type": "boolean"},
        
        # Media Info
        "duration_seconds": {"type": "integer"},
        "page_count": {"type": "integer"},
        "word_count": {"type": "integer"},
        
        # Ownership
        "owner_id": {"type": "keyword"},
        "institution_id": {"type": "keyword"},
        
        # Licensing
        "license_type": {"type": "keyword"},
        "source_name": {"type": "keyword"},
        
        # Tags & Keywords
        "tags": {"type": "keyword"},
        "subjects": {"type": "keyword"},
        "keywords": {"type": "keyword"},
        
        # Authors & Attribution
        "authors": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
            },
        },
        "publisher": {"type": "keyword"},
        
        # Metadata
        "metadata": {"type": "object", "enabled": False},
        
        # Timestamps
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "publication_year": {"type": "integer"},
        
        # Full text for search
        "full_text": {
            "type": "text",
            "analyzer": "text_analyzer",
        },
    },
}


class ContentIndexer:
    """
    Indexer for content documents in Elasticsearch.
    """
    
    def __init__(self, es_client: ElasticsearchClient | None = None):
        """Initialize the content indexer."""
        self._es = es_client
    
    async def get_client(self) -> ElasticsearchClient:
        """Get the Elasticsearch client."""
        if self._es is None:
            self._es = await get_es_client()
        return self._es
    
    async def create_index(self, recreate: bool = False) -> bool:
        """
        Create the content index with mappings.
        
        Args:
            recreate: If True, delete and recreate the index
        
        Returns:
            True if successful
        """
        es = await self.get_client()
        
        if recreate and await es.index_exists(CONTENT_INDEX):
            await es.delete_index(CONTENT_INDEX)
            logger.info("index_deleted_for_recreate", index=CONTENT_INDEX)
        
        return await es.create_index(
            index_name=CONTENT_INDEX,
            mappings=CONTENT_MAPPINGS,
            settings=INDEX_SETTINGS,
        )
    
    async def index_content(self, content: dict[str, Any]) -> bool:
        """
        Index a single content document.
        
        Args:
            content: Content document to index
        
        Returns:
            True if successful
        """
        es = await self.get_client()
        doc_id = str(content.get("id", uuid.uuid4()))
        
        # Prepare document for indexing
        doc = self._prepare_document(content)
        
        return await es.index_document(
            index_name=CONTENT_INDEX,
            doc_id=doc_id,
            document=doc,
        )
    
    async def index_content_batch(
        self,
        contents: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """
        Bulk index multiple content documents.
        
        Args:
            contents: List of content documents to index
        
        Returns:
            Tuple of (success_count, error_count)
        """
        es = await self.get_client()
        
        # Prepare documents
        docs = [self._prepare_document(c) for c in contents]
        
        return await es.bulk_index(
            index_name=CONTENT_INDEX,
            documents=docs,
            id_field="id",
        )
    
    async def update_content(self, content_id: str, updates: dict[str, Any]) -> bool:
        """
        Update an indexed content document.
        
        Args:
            content_id: Content UUID
            updates: Fields to update
        
        Returns:
            True if successful
        """
        es = await self.get_client()
        
        return await es.update_document(
            index_name=CONTENT_INDEX,
            doc_id=content_id,
            update=updates,
        )
    
    async def delete_content(self, content_id: str) -> bool:
        """
        Delete a content document from the index.
        
        Args:
            content_id: Content UUID
        
        Returns:
            True if successful
        """
        es = await self.get_client()
        
        return await es.delete_document(
            index_name=CONTENT_INDEX,
            doc_id=content_id,
        )
    
    async def reindex_all(self, contents: list[dict[str, Any]]) -> bool:
        """
        Reindex all content (delete and recreate).
        
        Args:
            contents: All content documents to index
        
        Returns:
            True if successful
        """
        es = await self.get_client()
        
        # Delete and recreate index
        await es.delete_index(CONTENT_INDEX)
        await es.create_index(
            index_name=CONTENT_INDEX,
            mappings=CONTENT_MAPPINGS,
            settings=INDEX_SETTINGS,
        )
        
        # Bulk index all content
        success, errors = await self.index_content_batch(contents)
        
        logger.info(
            "reindex_complete",
            total=len(contents),
            success=success,
            errors=errors,
        )
        
        # Refresh index
        await es.refresh_index(CONTENT_INDEX)
        
        return errors == 0
    
    def _prepare_document(self, content: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare a content document for indexing.
        
        Args:
            content: Raw content document
        
        Returns:
            Prepared document with all required fields
        """
        # Build full text from title, description, and summary
        full_text_parts = []
        
        if title := content.get("title"):
            full_text_parts.append(title)
        if desc := content.get("description"):
            full_text_parts.append(desc)
        if summary := content.get("summary"):
            full_text_parts.append(summary)
        if authors := content.get("authors"):
            if isinstance(authors, list):
                full_text_parts.extend(authors)
            else:
                full_text_parts.append(str(authors))
        
        # Build document
        doc = {
            "id": str(content.get("id", "")),
            "title": content.get("title", ""),
            "description": content.get("description"),
            "summary": content.get("summary"),
            "category": content.get("category"),
            "content_type": content.get("content_type"),
            "education_level": content.get("education_level"),
            "language": content.get("language", "en"),
            "is_public": content.get("is_public", False),
            "is_featured": content.get("is_featured", False),
            "is_premium": content.get("is_premium", False),
            "duration_seconds": content.get("duration_seconds"),
            "page_count": content.get("page_count"),
            "word_count": content.get("word_count"),
            "owner_id": str(content["owner_id"]) if content.get("owner_id") else None,
            "institution_id": str(content["institution_id"]) if content.get("institution_id") else None,
            "license_type": content.get("license_type"),
            "source_name": content.get("source_name"),
            "tags": content.get("tags") or [],
            "subjects": content.get("subjects") or [],
            "keywords": content.get("keywords") or [],
            "authors": content.get("authors") or [],
            "publisher": content.get("publisher"),
            "metadata": content.get("metadata") or {},
            "created_at": self._format_date(content.get("created_at")),
            "updated_at": self._format_date(content.get("updated_at")),
            "publication_year": content.get("publication_year"),
            "full_text": " ".join(full_text_parts),
        }
        
        return doc
    
    def _format_date(self, date_value: Any) -> str | None:
        """Format a date value for Elasticsearch."""
        if date_value is None:
            return None
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        if isinstance(date_value, str):
            return date_value
        return str(date_value)


async def index_content_from_db(
    db_session,
    batch_size: int = 1000,
) -> tuple[int, int]:
    """
    Index all content from database.
    
    Args:
        db_session: Database session
        batch_size: Number of documents per batch
    
    Returns:
        Tuple of (success_count, error_count)
    """
    from sqlalchemy import select
    from src.models.content import Content
    
    indexer = ContentIndexer()
    await indexer.create_index(recreate=False)
    
    total_success = 0
    total_errors = 0
    offset = 0
    
    while True:
        # Fetch batch from database
        query = (
            select(Content)
            .where(Content.deleted_at.is_(None))
            .offset(offset)
            .limit(batch_size)
        )
        result = await db_session.execute(query)
        contents = result.scalars().all()
        
        if not contents:
            break
        
        # Convert to dicts
        content_dicts = []
        for c in contents:
            content_dicts.append({
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "summary": c.summary,
                "category": c.category,
                "content_type": c.content_type,
                "education_level": c.education_level,
                "language": c.language,
                "is_public": c.is_public,
                "is_featured": c.is_featured,
                "is_premium": c.is_premium,
                "duration_seconds": c.duration_seconds,
                "page_count": c.page_count,
                "word_count": c.word_count,
                "owner_id": c.owner_id,
                "institution_id": c.institution_id,
                "license_type": c.license_type,
                "source_name": c.source_name,
                "tags": c.tags,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
            })
        
        # Index batch
        success, errors = await indexer.index_content_batch(content_dicts)
        total_success += success
        total_errors += errors
        
        offset += batch_size
        logger.info("indexing_progress", offset=offset, success=success, errors=errors)
    
    return total_success, total_errors
