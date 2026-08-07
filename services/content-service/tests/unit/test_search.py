"""
PANDORA Content Service Unit Tests - Search
Comprehensive tests for search components
"""
import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.search.reranker import (
    RRFScorer,
    HybridScorer,
    BoostingReranker,
    LearningToRankScorer,
    create_default_reranker,
    RRF_K,
)
from src.search.query_builder import (
    SearchFilters,
    SearchResult,
    ContentQueryBuilder,
    HIGHLIGHT_CONFIG,
    AGGREGATIONS,
)


pytestmark = pytest.mark.unit


# ============ RRF Scorer Tests ============

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
        
        ranking1 = [
            {"id": "1", "title": "Doc 1"},
            {"id": "2", "title": "Doc 2"},
            {"id": "3", "title": "Doc 3"},
        ]
        ranking2 = [
            {"id": "2", "title": "Doc 2"},
            {"id": "1", "title": "Doc 1"},
            {"id": "3", "title": "Doc 3"},
        ]
        
        result = scorer.fuse([ranking1, ranking2])
        
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
        
        assert result_low[0]["rrf_score"] > result_high[0]["rrf_score"]
    
    def test_rrf_empty_rankings(self):
        """Test RRF with empty rankings."""
        scorer = RRFScorer()
        result = scorer.fuse([])
        assert result == []
    
    def test_rrf_preserves_source(self):
        """Test that source data is preserved."""
        scorer = RRFScorer()
        ranking = [{"id": "1", "title": "Doc 1", "source": {"custom": "data"}}]
        
        result = scorer.fuse([ranking])
        
        assert result[0]["source"]["custom"] == "data"
    
    def test_rrf_tracks_individual_ranks(self):
        """Test that individual rankings are tracked."""
        scorer = RRFScorer()
        ranking1 = [{"id": "1"}, {"id": "2"}]
        ranking2 = [{"id": "2"}, {"id": "1"}]
        
        result = scorer.fuse([ranking1, ranking2])
        
        assert "rank_0" in result[0]
        assert "rank_1" in result[0]
    
    def test_rrf_calculates_correct_scores(self):
        """Test RRF score calculation."""
        scorer = RRFScorer(k=60)
        ranking = [{"id": "1"}, {"id": "2"}]
        
        result = scorer.fuse([ranking])
        
        # Score for rank 1: 1/(60+1) = 0.01639
        # Score for rank 2: 1/(60+2) = 0.01613
        assert result[0]["rrf_score"] == pytest.approx(1.0 / 61)
        assert result[1]["rrf_score"] == pytest.approx(1.0 / 62)


# ============ Hybrid Scorer Tests ============

class TestHybridScorer:
    """Tests for hybrid scorer."""
    
    def test_combine_scores_vector_and_lexical(self):
        """Test combining vector and lexical scores."""
        scorer = HybridScorer(
            vector_weight=0.5,
            lexical_weight=0.5,
            popularity_weight=0.0,
            freshness_weight=0.0,
        )
        
        results = [
            {"id": "1", "vector_similarity": 0.9, "bm25_score": 0.8},
            {"id": "2", "vector_similarity": 0.7, "bm25_score": 0.95},
        ]
        
        result = scorer.combine_scores(results)
        
        assert result[0]["combined_score"] == pytest.approx(0.85)
        assert result[1]["combined_score"] == pytest.approx(0.825)
    
    def test_weight_normalization(self):
        """Test that weights are normalized."""
        scorer = HybridScorer(
            vector_weight=2.0,
            lexical_weight=2.0,
            popularity_weight=0.0,
            freshness_weight=0.0,
        )
        
        assert scorer.vector_weight == 0.5
        assert scorer.lexical_weight == 0.5
    
    def test_elasticsearch_score_normalization(self):
        """Test Elasticsearch score normalization."""
        scorer = HybridScorer()
        
        # Very high Elasticsearch score
        high_score = scorer._normalize_elasticsearch_score(100.0)
        assert high_score <= 1.0
        assert high_score > 0
        
        # Zero score
        zero_score = scorer._normalize_elasticsearch_score(0)
        assert zero_score == 0
        
        # Negative score
        neg_score = scorer._normalize_elasticsearch_score(-5.0)
        assert neg_score == 0
    
    def test_combined_with_elasticsearch_score(self):
        """Test combining with Elasticsearch _score."""
        scorer = HybridScorer(
            vector_weight=0.0,
            lexical_weight=1.0,
            popularity_weight=0.0,
            freshness_weight=0.0,
        )
        
        results = [
            {"id": "1", "_score": 10.0},
        ]
        
        result = scorer.combine_scores(results)
        
        assert "combined_score" in result[0]
        assert result[0]["combined_score"] > 0
    
    def test_combined_with_popularity(self):
        """Test combining with popularity score."""
        scorer = HybridScorer(
            vector_weight=0.0,
            lexical_weight=0.0,
            popularity_weight=1.0,
            freshness_weight=0.0,
        )
        
        results = [
            {"id": "1", "popularity_score": 0.8},
        ]
        
        result = scorer.combine_scores(results)
        
        assert result[0]["combined_score"] == 0.8
    
    def test_empty_results(self):
        """Test with empty results."""
        scorer = HybridScorer()
        result = scorer.combine_scores([])
        assert result == []


# ============ Boosting Reranker Tests ============

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
        
        assert reranked[0]["id"] == "1"
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
            {"id": "1", "source": {"is_featured": True, "is_public": True}, "_score": 1.0},
        ]
        
        reranked = reranker.rerank(results)
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
    
    def test_no_boosts(self):
        """Test reranker with no boosts."""
        reranker = BoostingReranker()
        results = [{"id": "1", "_score": 1.0}]
        
        reranked = reranker.rerank(results)
        
        assert reranked[0]["boosted_score"] == 1.0
    
    def test_none_context(self):
        """Test with None context."""
        reranker = BoostingReranker()
        results = [{"id": "1", "_score": 1.0}]
        
        reranked = reranker.rerank(results, context=None)
        
        assert reranked[0]["boosted_score"] == 1.0
    
    def test_high_rating_boost(self):
        """Test boost for high-rated content."""
        reranker = create_default_reranker()
        
        results = [
            {"id": "1", "source": {"metadata_record": {"average_rating": 4.5}}, "_score": 1.0},
            {"id": "2", "source": {"metadata_record": {"average_rating": 3.0}}, "_score": 1.0},
        ]
        
        reranked = reranker.rerank(results)
        
        assert reranked[0]["id"] == "1"
        assert reranked[0]["boosted_score"] == 1.3


# ============ Learning to Rank Scorer Tests ============

class TestLearningToRankScorer:
    """Tests for Learning to Rank scorer."""
    
    def test_score_features(self):
        """Test scoring with features."""
        scorer = LearningToRankScorer(
            feature_weights={
                "relevance": 0.5,
                "popularity": 0.5,
            }
        )
        
        features = {"relevance": 0.8, "popularity": 0.6}
        score = scorer.score(features)
        
        assert score == pytest.approx(0.7)  # 0.5*0.8 + 0.5*0.6
    
    def test_rank_results(self):
        """Test ranking results."""
        scorer = LearningToRankScorer()
        
        def extractor(result):
            return {"relevance": result.get("relevance", 0)}
        
        results = [
            {"id": "1", "relevance": 0.3},
            {"id": "2", "relevance": 0.9},
        ]
        
        ranked = scorer.rank(results, extractor)
        
        assert ranked[0]["id"] == "2"
        assert ranked[0]["ltr_score"] > ranked[1]["ltr_score"]
    
    def test_default_weights(self):
        """Test default feature weights."""
        scorer = LearningToRankScorer()
        
        assert "relevance" in scorer.feature_weights
        assert "popularity" in scorer.feature_weights
        assert sum(scorer.feature_weights.values()) == 1.0


# ============ SearchFilters Tests ============

class TestSearchFilters:
    """Tests for SearchFilters."""
    
    def test_filters_defaults(self):
        """Test default filter values."""
        filters = SearchFilters()
        
        assert filters.query is None
        assert filters.category is None
        assert filters.is_public is None
        assert filters.tags is None
    
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
            language=["en", "es"],
        )
        
        assert filters.category == ["course", "book"]
        assert filters.tags == ["ai", "ml"]
        assert filters.language == ["en", "es"]
    
    def test_filters_date_range(self):
        """Test date range filters."""
        filters = SearchFilters(
            date_from="2024-01-01",
            date_to="2024-12-31",
        )
        
        assert filters.date_from == "2024-01-01"
        assert filters.date_to == "2024-12-31"
    
    def test_filters_ownership(self):
        """Test ownership filters."""
        filters = SearchFilters(
            owner_id="user-123",
            institution_id="inst-456",
        )
        
        assert filters.owner_id == "user-123"
        assert filters.institution_id == "inst-456"
    
    def test_filters_visibility(self):
        """Test visibility filters."""
        filters = SearchFilters(
            is_public=True,
            is_featured=False,
            is_premium=True,
        )
        
        assert filters.is_public is True
        assert filters.is_featured is False
        assert filters.is_premium is True


# ============ SearchResult Tests ============

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
    
    def test_to_dict_no_aggregations(self):
        """Test SearchResult without aggregations."""
        result = SearchResult(total=0, hits=[])
        
        d = result.to_dict()
        
        assert d["total"] == 0
        assert d["aggregations"] is None


# ============ Query Builder Tests ============

class TestContentQueryBuilder:
    """Tests for ContentQueryBuilder."""
    
    def test_build_query_empty(self):
        """Test building query with no filters."""
        builder = ContentQueryBuilder()
        filters = SearchFilters()
        
        query = builder.build_query(filters)
        
        assert "match_all" in query
    
    def test_build_query_with_text(self):
        """Test building query with text search."""
        builder = ContentQueryBuilder()
        filters = SearchFilters(query="machine learning")
        
        query = builder.build_query(filters)
        
        assert "bool" in query
        assert "must" in query["bool"]
        assert "multi_match" in query["bool"]["must"][0]
    
    def test_build_query_with_category(self):
        """Test building query with category filter."""
        builder = ContentQueryBuilder()
        filters = SearchFilters(category="course")
        
        query = builder.build_query(filters)
        
        assert "bool" in query
        assert "filter" in query["bool"]
    
    def test_build_query_with_education_level(self):
        """Test building query with education level."""
        builder = ContentQueryBuilder()
        filters = SearchFilters(education_level="undergraduate")
        
        query = builder.build_query(filters)
        
        assert "bool" in query
    
    def test_build_query_with_date_range(self):
        """Test building query with date range."""
        builder = ContentQueryBuilder()
        filters = SearchFilters(date_from="2024-01-01", date_to="2024-12-31")
        
        query = builder.build_query(filters)
        
        assert "bool" in query
        assert "filter" in query["bool"]
    
    def test_build_sort_default(self):
        """Test default sort."""
        builder = ContentQueryBuilder()
        
        sort = builder.build_sort()
        
        assert len(sort) == 2
        assert "_score" in sort[0]
    
    def test_build_sort_by_date(self):
        """Test sort by date."""
        builder = ContentQueryBuilder()
        
        sort = builder.build_sort(sort_by="date", sort_order="asc")
        
        assert "created_at" in sort[0]
    
    def test_terms_filter_single_value(self):
        """Test terms filter with single value."""
        builder = ContentQueryBuilder()
        
        result = builder._terms_filter("category", "course")
        
        assert "term" in result
        assert result["term"]["category"] == "course"
    
    def test_terms_filter_list_value(self):
        """Test terms filter with list value."""
        builder = ContentQueryBuilder()
        
        result = builder._terms_filter("category", ["course", "book"])
        
        assert "terms" in result
        assert result["terms"]["category"] == ["course", "book"]


# ============ Highlight Config Tests ============

class TestHighlightConfig:
    """Tests for highlight configuration."""
    
    def test_highlight_fields(self):
        """Test highlight configuration has required fields."""
        assert "fields" in HIGHLIGHT_CONFIG
        assert "title" in HIGHLIGHT_CONFIG["fields"]
        assert "description" in HIGHLIGHT_CONFIG["fields"]
    
    def test_highlight_tags(self):
        """Test highlight pre/post tags."""
        assert HIGHLIGHT_CONFIG["pre_tags"] == ["<mark>"]
        assert HIGHLIGHT_CONFIG["post_tags"] == ["</mark>"]


# ============ Aggregations Tests ============

class TestAggregations:
    """Tests for aggregation configuration."""
    
    def test_aggregations_keys(self):
        """Test aggregation keys exist."""
        assert "categories" in AGGREGATIONS
        assert "content_types" in AGGREGATIONS
        assert "education_levels" in AGGREGATIONS
        assert "languages" in AGGREGATIONS
    
    def test_aggregation_structure(self):
        """Test aggregation structure."""
        for name, agg in AGGREGATIONS.items():
            assert "terms" in agg
            assert "field" in agg["terms"]
            assert "size" in agg["terms"]


# ============ Default Reranker Tests ============

class TestCreateDefaultReranker:
    """Tests for create_default_reranker function."""
    
    def test_creates_reranker(self):
        """Test that default reranker is created."""
        reranker = create_default_reranker()
        
        assert isinstance(reranker, BoostingReranker)
    
    def test_has_boosts(self):
        """Test that default reranker has boosts."""
        reranker = create_default_reranker()
        
        # Should have boosts for featured, public, high-rated
        assert len(reranker.boosts) >= 3
