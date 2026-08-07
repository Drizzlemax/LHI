"""PANDORA Content Service Search Module."""
from src.search.client import (
    ElasticsearchClient,
    get_es_client,
    close_es_client,
)
from src.search.indexer import (
    ContentIndexer,
    CONTENT_INDEX,
    CONTENT_MAPPINGS,
    INDEX_SETTINGS,
    index_content_from_db,
)
from src.search.query_builder import (
    SearchFilters,
    SearchResult,
    ContentQueryBuilder,
    CONTENT_INDEX as SEARCH_CONTENT_INDEX,
    search_content,
)
from src.search.reranker import (
    RRFScorer,
    HybridScorer,
    LearningToRankScorer,
    BoostingReranker,
    create_default_reranker,
    RRF_K,
)

__all__ = [
    # Client
    "ElasticsearchClient",
    "get_es_client",
    "close_es_client",
    # Indexer
    "ContentIndexer",
    "CONTENT_INDEX",
    "CONTENT_MAPPINGS",
    "INDEX_SETTINGS",
    "index_content_from_db",
    # Query Builder
    "SearchFilters",
    "SearchResult",
    "ContentQueryBuilder",
    "SEARCH_CONTENT_INDEX",
    "search_content",
    # Reranker
    "RRFScorer",
    "HybridScorer",
    "LearningToRankScorer",
    "BoostingReranker",
    "create_default_reranker",
    "RRF_K",
]