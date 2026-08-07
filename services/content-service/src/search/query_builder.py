"""
PANDORA Content Service Search Query Builder
Full-text search with filters, aggregations, and highlighting
"""
from typing import Any

from src.search.client import ElasticsearchClient, get_es_client
from src.core.logging import get_logger

logger = get_logger(__name__)


# Index name constant
CONTENT_INDEX = "pandora_content"


# Highlight configuration
HIGHLIGHT_CONFIG = {
    "fields": {
        "title": {
            "number_of_fragments": 1,
            "fragment_size": 150,
        },
        "description": {
            "number_of_fragments": 3,
            "fragment_size": 150,
        },
        "summary": {
            "number_of_fragments": 2,
            "fragment_size": 150,
        },
        "full_text": {
            "number_of_fragments": 5,
            "fragment_size": 150,
        },
    },
    "pre_tags": ["<mark>"],
    "post_tags": ["</mark>"],
}


# Aggregation definitions
AGGREGATIONS = {
    "categories": {
        "terms": {
            "field": "category",
            "size": 20,
        }
    },
    "content_types": {
        "terms": {
            "field": "content_type",
            "size": 20,
        }
    },
    "education_levels": {
        "terms": {
            "field": "education_level",
            "size": 10,
        }
    },
    "languages": {
        "terms": {
            "field": "language",
            "size": 50,
        }
    },
    "license_types": {
        "terms": {
            "field": "license_type",
            "size": 20,
        }
    },
    "popular_tags": {
        "terms": {
            "field": "tags",
            "size": 30,
        }
    },
    "authors": {
        "terms": {
            "field": "authors.keyword",
            "size": 20,
        }
    },
}


class SearchFilters:
    """Search filter parameters."""
    
    def __init__(
        self,
        query: str | None = None,
        category: str | list[str] | None = None,
        content_type: str | list[str] | None = None,
        education_level: str | list[str] | None = None,
        language: str | list[str] | None = None,
        license_type: str | list[str] | None = None,
        tags: list[str] | None = None,
        is_public: bool | None = None,
        is_featured: bool | None = None,
        is_premium: bool | None = None,
        owner_id: str | None = None,
        institution_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        self.query = query
        self.category = category
        self.content_type = content_type
        self.education_level = education_level
        self.language = language
        self.license_type = license_type
        self.tags = tags
        self.is_public = is_public
        self.is_featured = is_featured
        self.is_premium = is_premium
        self.owner_id = owner_id
        self.institution_id = institution_id
        self.date_from = date_from
        self.date_to = date_to


class SearchResult:
    """Structured search result."""
    
    def __init__(
        self,
        total: int,
        hits: list[dict[str, Any]],
        aggregations: dict[str, Any] | None = None,
        took_ms: int = 0,
    ):
        self.total = total
        self.hits = hits
        self.aggregations = aggregations
        self.took_ms = took_ms
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total,
            "hits": self.hits,
            "aggregations": self.aggregations,
            "took_ms": self.took_ms,
        }


class ContentQueryBuilder:
    """
    Query builder for content search.
    """
    
    def __init__(self, es_client: ElasticsearchClient | None = None):
        """Initialize query builder."""
        self._es = es_client
    
    async def get_client(self) -> ElasticsearchClient:
        """Get the Elasticsearch client."""
        if self._es is None:
            self._es = await get_es_client()
        return self._es
    
    def build_query(self, filters: SearchFilters) -> dict[str, Any]:
        """
        Build an Elasticsearch query from filters.
        
        Args:
            filters: Search filter parameters
        
        Returns:
            Elasticsearch query dict
        """
        must_clauses: list[dict[str, Any]] = []
        filter_clauses: list[dict[str, Any]] = []
        
        # Full-text search
        if filters.query:
            must_clauses.append({
                "multi_match": {
                    "query": filters.query,
                    "fields": [
                        "title^3",
                        "title.autocomplete^2",
                        "description^2",
                        "summary",
                        "full_text",
                        "authors^1.5",
                        "tags",
                        "subjects",
                        "keywords",
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "prefix_length": 2,
                }
            })
        
        # Category filter
        if filters.category:
            filter_clauses.append(self._terms_filter("category", filters.category))
        
        # Content type filter
        if filters.content_type:
            filter_clauses.append(self._terms_filter("content_type", filters.content_type))
        
        # Education level filter
        if filters.education_level:
            filter_clauses.append(self._terms_filter("education_level", filters.education_level))
        
        # Language filter
        if filters.language:
            filter_clauses.append(self._terms_filter("language", filters.language))
        
        # License type filter
        if filters.license_type:
            filter_clauses.append(self._terms_filter("license_type", filters.license_type))
        
        # Tags filter
        if filters.tags:
            filter_clauses.append({
                "terms": {"tags": filters.tags}
            })
        
        # Visibility filters
        if filters.is_public is not None:
            filter_clauses.append({"term": {"is_public": filters.is_public}})
        if filters.is_featured is not None:
            filter_clauses.append({"term": {"is_featured": filters.is_featured}})
        if filters.is_premium is not None:
            filter_clauses.append({"term": {"is_premium": filters.is_premium}})
        
        # Ownership filters
        if filters.owner_id:
            filter_clauses.append({"term": {"owner_id": filters.owner_id}})
        if filters.institution_id:
            filter_clauses.append({"term": {"institution_id": filters.institution_id}})
        
        # Date range filter
        if filters.date_from or filters.date_to:
            date_range: dict[str, Any] = {}
            if filters.date_from:
                date_range["gte"] = filters.date_from
            if filters.date_to:
                date_range["lte"] = filters.date_to
            filter_clauses.append({"range": {"created_at": date_range}})
        
        # Build the final query
        if must_clauses or filter_clauses:
            return {
                "bool": {
                    "must": must_clauses if must_clauses else [{"match_all": {}}],
                    "filter": filter_clauses,
                }
            }
        else:
            return {"match_all": {}}
    
    def _terms_filter(
        self,
        field: str,
        value: str | list[str],
    ) -> dict[str, Any]:
        """Create a terms filter."""
        if isinstance(value, list):
            return {"terms": {field: value}}
        return {"term": {field: value}}
    
    def build_sort(
        self,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[dict[str, Any]]:
        """Build sort clause."""
        if not sort_by:
            return [{"_score": {"order": "desc"}}, {"created_at": {"order": "desc"}}]
        
        sort_mapping = {
            "relevance": [{"_score": {"order": "desc"}}],
            "date": [{"created_at": {"order": sort_order}}],
            "title": [{"title.keyword": {"order": sort_order}}],
            "popularity": [{"view_count": {"order": "desc"}}],
        }
        
        return sort_mapping.get(sort_by, [{"_score": {"order": "desc"}}])
    
    async def search(
        self,
        filters: SearchFilters,
        skip: int = 0,
        limit: int = 20,
        sort_by: str | None = None,
        sort_order: str = "desc",
        include_aggregations: bool = True,
    ) -> SearchResult:
        """
        Execute a search query.
        
        Args:
            filters: Search filters
            skip: Number of results to skip
            limit: Maximum results to return
            sort_by: Sort field
            sort_order: Sort direction (asc/desc)
            include_aggregations: Include facet aggregations
        
        Returns:
            SearchResult with hits and metadata
        """
        es = await self.get_client()
        
        query = self.build_query(filters)
        sort = self.build_sort(sort_by, sort_order)
        
        aggs = AGGREGATIONS if include_aggregations else None
        
        result = await es.search(
            index_name=CONTENT_INDEX,
            query=query,
            size=limit,
            from_=skip,
            sort=sort,
            highlight=HIGHLIGHT_CONFIG,
            aggs=aggs,
        )
        
        return SearchResult(
            total=result["total"],
            hits=result["hits"],
            aggregations=result.get("aggregations"),
        )
    
    async def suggest(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Get search suggestions (autocomplete).
        
        Args:
            query: Partial search query
            limit: Maximum suggestions
        
        Returns:
            List of suggestions with titles
        """
        es = await self.get_client()
        
        es_query = {
            "bool": {
                "should": [
                    {
                        "match_phrase_prefix": {
                            "title": {
                                "query": query,
                                "boost": 2,
                            }
                        }
                    },
                    {
                        "match": {
                            "title.autocomplete": {
                                "query": query,
                            }
                        }
                    },
                ]
            }
        }
        
        result = await es.search(
            index_name=CONTENT_INDEX,
            query=es_query,
            size=limit,
        )
        
        return [
            {
                "id": hit["_id"],
                "title": hit["_source"].get("title", ""),
                "category": hit["_source"].get("category"),
            }
            for hit in result["hits"]
        ]
    
    async def more_like_this(
        self,
        content_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find similar content using More Like This.
        
        Args:
            content_id: Content ID to find similar items to
            limit: Maximum results
        
        Returns:
            List of similar content
        """
        es = await self.get_client()
        
        query = {
            "more_like_this": {
                "fields": [
                    "title",
                    "description",
                    "summary",
                    "tags",
                    "subjects",
                ],
                "like": [
                    {
                        "_index": CONTENT_INDEX,
                        "_id": content_id,
                    }
                ],
                "min_term_freq": 1,
                "min_doc_freq": 1,
            }
        }
        
        result = await es.search(
            index_name=CONTENT_INDEX,
            query=query,
            size=limit,
        )
        
        return result["hits"]
    
    async def search_by_vector(
        self,
        vector: list[float],
        limit: int = 10,
        min_score: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Search by embedding vector.
        
        Args:
            vector: Query embedding vector
            limit: Maximum results
            min_score: Minimum similarity score
        
        Returns:
            List of similar content
        """
        es = await self.get_client()
        
        query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": vector},
                },
            }
        }
        
        result = await es.search(
            index_name=CONTENT_INDEX,
            query=query,
            size=limit,
        )
        
        # Filter by minimum score
        hits = [
            hit for hit in result["hits"]
            if hit["score"] >= min_score
        ]
        
        return hits


async def search_content(
    filters: SearchFilters,
    skip: int = 0,
    limit: int = 20,
    sort_by: str | None = None,
    sort_order: str = "desc",
) -> SearchResult:
    """
    Convenience function for content search.
    
    Args:
        filters: Search filters
        skip: Number of results to skip
        limit: Maximum results
        sort_by: Sort field
        sort_order: Sort direction
    
    Returns:
        SearchResult
    """
    builder = ContentQueryBuilder()
    return await builder.search(
        filters=filters,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
