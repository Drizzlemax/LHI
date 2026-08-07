"""
PANDORA Content Service Unit Tests - Search
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.search.reranker import (
    RRFScorer,
    HybridScorer,
    BoostingReranker,
    RRF_K,
)
from src.search.query_builder import SearchFilters, SearchResult


pytestmark = pytest.mark.unit


class TestRRFScorer:
    """Tests for Reciprocal Rank Fusion scorer."""
    
    def test_rrf_single_ranking(self):
        """Test RRF with single ranking."""
        scorer = RRFScorer(k=RRF_K)
        ranking = [
            {"id": "1", "title": "Doc 1"},
            {"id": "2", "title": "Doc 2"},
            {"id": "3", "title": "Doc 3"},
        ]
        
        result = scorer.fuse([ranking])
        
        assert len(result) == 3
        assert result[0]["id"] == "1"
        assert "rrf_score" in result[0]
    
    def test_rrf_multiple_rankings(self):
        """Test RRF with multiple rankings."""
        scorer = RRFScorer(k=RRF_K)
        
        # First ranking: 1, 2, 3
        ranking1 = [
            {"id": "1", "title": "Doc 1"},
            {"id": "2", "title": "Doc 2"},
            {"id": "3", "title": "Doc 3"},
        ]
        
        # Second ranking: 2, 1, 3
        ranking2 = [
            {"id": "2", "title": "Doc 2"},
            {"id": "1", "title": "Doc 1"},
            {"id": "3", "title": "Doc 3"},
        ]
        
        result = scorer.fuse([ranking1, ranking2])
        
        # Doc 1 should rank first (rank 1 + rank 2)
        # Doc 2 should rank second (rank 2 + rank 1)
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"
    
    def test_rrf_different_k_values(self):
        """Test RRF with different K values."""
        ranking = [
            {"id": "1", "title": "Doc 1"},
            {"id": "2", "title": "Doc 2"},
        ]
        
        scorer_low_k = RRFScorer(k=10)
        scorer_high_k = RRFScorer(k=100)
        
        result_low = scorer_low_k.fuse([ranking])
        result_high = scorer_high_k.fuse([ranking])
        
        # Higher K reduces the impact of rank differences
        assert result_low[0]["rrf_score"] > result_high[0]["rrf_score"]
    
    def test_rrf_empty_rankings(self):
        """Test RRF with empty rankings."""
        scorer = RRFScorer()
        result = scorer.fuse([])
        assert result == []


class TestHybridScorer:
    """Tests for hybrid scorer."""
    
    def test_combine_scores(self):
        """Test combining multiple scores."""
        scorer = HybridScorer(
            vector_weight=0.5,
            lexical_weight=0.5,
            popularity_weight=0.0,
            freshness_weight=0.0,
        )
        
        results = [
            {
                "id": "1",
                "vector_similarity": 0.9,
                "bm25_score": 0.8,
            },
            {
                "id": "2",
                "vector_similarity": 0.7,
                "bm25_score": 0.95,
            },
        ]
        
        result = scorer.combine_scores(results)
        
        assert len(result) == 2
        assert "combined_score" in result[0]
        # First doc: 0.5 * 0.9 + 0.5 * 0.8 = 0.85
        # Second doc: 0.5 * 0.7 + 0.5 * 0.95 = 0.825
        assert result[0]["combined_score"] == pytest.approx(0.85)
    
    def test_weight_normalization(self):
        """Test that weights are normalized."""
        scorer = HybridScorer(
            vector_weight=2.0,
            lexical_weight=2.0,
            popularity_weight=0.0,
            freshness_weight=0.0,
        )
        
        # Weights should be normalized to 0.5 each
        assert scorer.vector_weight == 0.5
        assert scorer.lexical_weight == 0.5


class TestBoostingReranker:
    """Tests for boosting reranker."""
    
    def test_featured_boost(self):
        """Test boosting featured content."""
        reranker = BoostingReranker()
        reranker.add_boost(
            condition=lambda r, c: r.get("source", {}).get("is_featured", False),
            factor=1.5,
            description="Featured boost",
        )
        
        results = [
            {"id": "1", "source": {"is_featured": True}, "_score": 1.0},
            {"id": "2", "source": {"is_featured": False}, "_score": 1.0},
        ]
        
        reranked = reranker.rerank(results)
        
        assert reranked[0]["id"] == "1"  # Featured should rank first
        assert reranked[0]["boosted_score"] == 1.5
        assert reranked[1]["boosted_score"] == 1.0
    
    def test_chain_boosts(self):
        """Test chaining multiple boosts."""
        reranker = BoostingReranker()
        reranker.add_boost(
            condition=lambda r, c: r.get("source", {}).get("is_featured", False),
            factor=1.5,
        ).add_boost(
            condition=lambda r, c: r.get("source", {}).get("is_public", False),
            factor=1.2,
        )
        
        results = [
            {
                "id": "1",
                "source": {"is_featured": True, "is_public": True},
                "_score": 1.0,
            },
        ]
        
        reranked = reranker.rerank(results)
        
        # 1.0 * 1.5 * 1.2 = 1.8
        assert reranked[0]["boosted_score"] == 1.8
    
    def test_context_boosts(self):
        """Test boosts based on context."""
        reranker = BoostingReranker()
        reranker.add_boost(
            condition=lambda r, c: c.get("user_prefers", []) and 
                                   r.get("source", {}).get("category") in c["user_prefers"],
            factor=2.0,
        )
        
        results = [
            {"id": "1", "source": {"category": "science"}, "_score": 1.0},
            {"id": "2", "source": {"category": "art"}, "_score": 1.0},
        ]
        
        reranked = reranker.rerank(results, context={"user_prefers": ["science"]})
        
        assert reranked[0]["id"] == "1"
        assert reranked[0]["boosted_score"] == 2.0


class TestSearchFilters:
    """Tests for SearchFilters."""
    
    def test_filters_defaults(self):
        """Test default filter values."""
        filters = SearchFilters()
        
        assert filters.query is None
        assert filters.category is None
        assert filters.is_public is None
    
    def test_filters_with_values(self):
        """Test filters with values."""
        filters = SearchFilters(
            query="machine learning",
            category="course",
            education_level="undergraduate",
            is_public=True,
        )
        
        assert filters.query == "machine learning"
        assert filters.category == "course"
        assert filters.education_level == "undergraduate"
        assert filters.is_public is True
    
    def test_filters_list_values(self):
        """Test filters with list values."""
        filters = SearchFilters(
            category=["course", "book"],
            tags=["ai", "ml"],
        )
        
        assert filters.category == ["course", "book"]
        assert filters.tags == ["ai", "ml"]


class TestSearchResult:
    """Tests for SearchResult."""
    
    def test_to_dict(self):
        """Test SearchResult to dict conversion."""
        result = SearchResult(
            total=100,
            hits=[{"id": "1", "title": "Doc 1"}],
            aggregations={"categories": {"buckets": []}},
            took_ms=25,
        )
        
        d = result.to_dict()
        
        assert d["total"] == 100
        assert len(d["hits"]) == 1
        assert d["took_ms"] == 25
