"""
PANDORA Content Service Elasticsearch Client
Async Elasticsearch client with connection pooling and health checks
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from elasticsearch import AsyncElasticsearch, NotFoundError
from elasticsearch.helpers import async_bulk

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class ElasticsearchClient:
    """
    Async Elasticsearch client wrapper with connection pooling and health checks.
    """
    
    def __init__(self):
        """Initialize Elasticsearch client."""
        self._client: AsyncElasticsearch | None = None
        self._connected = False
    
    async def connect(self) -> None:
        """Establish connection to Elasticsearch."""
        if self._client is not None:
            return
        
        hosts = settings.elasticsearch_hosts or ["http://localhost:9200"]
        
        self._client = AsyncElasticsearch(
            hosts=hosts,
            verify_certs=settings.elasticsearch_verify_certs,
            ca_certs=settings.elasticsearch_ca_certs,
            basic_auth=(
                settings.elasticsearch_username,
                settings.elasticsearch_password,
            ) if settings.elasticsearch_username else None,
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )
        
        # Test connection
        try:
            info = await self._client.info()
            logger.info(
                "elasticsearch_connected",
                cluster_name=info["cluster_name"],
                version=info["version"]["number"],
            )
            self._connected = True
        except Exception as e:
            logger.error("elasticsearch_connection_failed", error=str(e))
            self._connected = False
            raise
    
    async def disconnect(self) -> None:
        """Close Elasticsearch connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
            self._connected = False
            logger.info("elasticsearch_disconnected")
    
    async def health_check(self) -> dict[str, Any]:
        """Check Elasticsearch cluster health."""
        if self._client is None:
            return {"status": "disconnected", "connected": False}
        
        try:
            health = await self._client.cluster.health()
            return {
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"],
                "active_shards": health["active_shards"],
                "connected": True,
            }
        except Exception as e:
            logger.error("elasticsearch_health_check_failed", error=str(e))
            return {"status": "error", "connected": False, "error": str(e)}
    
    @property
    def client(self) -> AsyncElasticsearch:
        """Get the Elasticsearch client."""
        if self._client is None:
            raise RuntimeError("Elasticsearch client not connected. Call connect() first.")
        return self._client
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._connected and self._client is not None
    
    async def index_exists(self, index_name: str) -> bool:
        """Check if an index exists."""
        try:
            return await self.client.indices.exists(index=index_name)
        except Exception as e:
            logger.error("index_exists_check_failed", index=index_name, error=str(e))
            return False
    
    async def create_index(
        self,
        index_name: str,
        mappings: dict[str, Any],
        settings: dict[str, Any] | None = None,
    ) -> bool:
        """Create an index with mappings and settings."""
        try:
            if await self.index_exists(index_name):
                logger.info("index_already_exists", index=index_name)
                return True
            
            body: dict[str, Any] = {"mappings": mappings}
            if settings:
                body["settings"] = settings
            
            await self.client.indices.create(index=index_name, body=body)
            logger.info("index_created", index=index_name)
            return True
        except Exception as e:
            logger.error("index_creation_failed", index=index_name, error=str(e))
            return False
    
    async def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        try:
            if not await self.index_exists(index_name):
                return True
            
            await self.client.indices.delete(index=index_name)
            logger.info("index_deleted", index=index_name)
            return True
        except Exception as e:
            logger.error("index_deletion_failed", index=index_name, error=str(e))
            return False
    
    async def index_document(
        self,
        index_name: str,
        doc_id: str,
        document: dict[str, Any],
        refresh: bool = False,
    ) -> bool:
        """Index a single document."""
        try:
            await self.client.index(
                index=index_name,
                id=doc_id,
                document=document,
                refresh=refresh,
            )
            return True
        except Exception as e:
            logger.error(
                "document_indexing_failed",
                index=index_name,
                doc_id=doc_id,
                error=str(e),
            )
            return False
    
    async def get_document(
        self,
        index_name: str,
        doc_id: str,
    ) -> dict[str, Any] | None:
        """Get a document by ID."""
        try:
            result = await self.client.get(index=index_name, id=doc_id)
            return result["_source"]
        except NotFoundError:
            return None
        except Exception as e:
            logger.error("document_get_failed", index=index_name, doc_id=doc_id, error=str(e))
            return None
    
    async def delete_document(
        self,
        index_name: str,
        doc_id: str,
        refresh: bool = False,
    ) -> bool:
        """Delete a document by ID."""
        try:
            await self.client.delete(index=index_name, id=doc_id, refresh=refresh)
            return True
        except NotFoundError:
            return True  # Already deleted
        except Exception as e:
            logger.error(
                "document_deletion_failed",
                index=index_name,
                doc_id=doc_id,
                error=str(e),
            )
            return False
    
    async def update_document(
        self,
        index_name: str,
        doc_id: str,
        update: dict[str, Any],
        refresh: bool = False,
    ) -> bool:
        """Update a document by ID."""
        try:
            await self.client.update(
                index=index_name,
                id=doc_id,
                doc=update,
                refresh=refresh,
            )
            return True
        except NotFoundError:
            logger.warning(
                "document_not_found_for_update",
                index=index_name,
                doc_id=doc_id,
            )
            return False
        except Exception as e:
            logger.error(
                "document_update_failed",
                index=index_name,
                doc_id=doc_id,
                error=str(e),
            )
            return False
    
    async def bulk_index(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
        id_field: str = "id",
        chunk_size: int = 500,
    ) -> tuple[int, int]:
        """
        Bulk index documents.
        
        Returns:
            Tuple of (success_count, error_count)
        """
        if not documents:
            return 0, 0
        
        def generate_actions():
            for doc in documents:
                yield {
                    "_index": index_name,
                    "_id": str(doc.get(id_field, doc.get("id"))),
                    "_source": doc,
                }
        
        try:
            success, errors = await async_bulk(
                self.client,
                generate_actions(),
                chunk_size=chunk_size,
                raise_on_error=False,
            )
            error_count = len(errors) if errors else 0
            logger.info(
                "bulk_index_complete",
                success=success,
                errors=error_count,
            )
            return success, error_count
        except Exception as e:
            logger.error("bulk_index_failed", error=str(e))
            return 0, len(documents)
    
    async def search(
        self,
        index_name: str,
        query: dict[str, Any],
        size: int = 20,
        from_: int = 0,
        sort: list[dict[str, Any]] | None = None,
        highlight: dict[str, Any] | None = None,
        aggs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a search query."""
        try:
            body: dict[str, Any] = {"query": query, "size": size, "from": from_}
            
            if sort:
                body["sort"] = sort
            if highlight:
                body["highlight"] = highlight
            if aggs:
                body["aggs"] = aggs
            
            result = await self.client.search(index=index_name, body=body)
            
            return {
                "total": result["hits"]["total"]["value"],
                "hits": [
                    {
                        "id": hit["_id"],
                        "score": hit["_score"],
                        "source": hit["_source"],
                        "highlight": hit.get("highlight"),
                    }
                    for hit in result["hits"]["hits"]
                ],
                "aggregations": result.get("aggregations"),
            }
        except Exception as e:
            logger.error("search_failed", index=index_name, error=str(e))
            return {"total": 0, "hits": [], "aggregations": None}
    
    async def count(
        self,
        index_name: str,
        query: dict[str, Any] | None = None,
    ) -> int:
        """Count documents matching a query."""
        try:
            body = {"query": query} if query else None
            result = await self.client.count(index=index_name, body=body)
            return result["count"]
        except Exception as e:
            logger.error("count_failed", index=index_name, error=str(e))
            return 0
    
    async def refresh_index(self, index_name: str) -> bool:
        """Refresh an index to make recent changes searchable."""
        try:
            await self.client.indices.refresh(index=index_name)
            return True
        except Exception as e:
            logger.error("index_refresh_failed", index=index_name, error=str(e))
            return False


# Global client instance
_es_client: ElasticsearchClient | None = None


async def get_es_client() -> ElasticsearchClient:
    """Get or create the global Elasticsearch client."""
    global _es_client
    if _es_client is None:
        _es_client = ElasticsearchClient()
        await _es_client.connect()
    return _es_client


async def close_es_client() -> None:
    """Close the global Elasticsearch client."""
    global _es_client
    if _es_client is not None:
        await _es_client.disconnect()
        _es_client = None
