"""
PANDORA Content Service Search Reranker
RRF (Reciprocal Rank Fusion) and hybrid score combination
"""
from typing import Any
from collections import defaultdict

from src.core.logging import get_logger

logger = get_logger(__name__)


# RRF constant (typically 60 works well for most use cases)
RRF_K = 60


class RRFScorer:
    """
    Reciprocal Rank Fusion (RRF) scorer.
    
    RRF combines multiple rankings into a single ranking without
    needing to normalize scores. It's particularly useful when
    combining lexical search with vector search.
    
    Formula: RRF_score(d) = Σ 1/(k + rank(d))
    
    Reference: https://arxiv.org/abs/1911.07617
    """
    
    def __init__(self, k: int = RRF_K):
        """
        Initialize RRF scorer.
        
        Args:
            k: RRF constant (default 60). Higher values reduce the
               impact of rank differences between result lists.
        """
        self.k = k
    
    def fuse(
        self,
        rankings: list[list[dict[str, Any]]],
        score_field: str = "score",
        rank_field: str = "rank",
    ) -> list[dict[str, Any]]:
        """
        Fuse multiple rankings using RRF.
        
        Args:
            rankings: List of result lists, each already sorted by relevance
            score_field: Field name for the fused RRF score in output
            rank_field: Field name for individual rankings in output
        
        Returns:
            Fused and reranked results
        """
        if not rankings:
            return []
        
        if len(rankings) == 1:
            # Single ranking, just add scores
            return self._add_rrf_scores(rankings[0], [1.0], score_field)
        
        # Aggregate scores by document ID
        doc_scores: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "rrf_score": 0.0,
            rank_field: {},
        })
        
        # Calculate RRF scores for each ranking
        for ranking_idx, ranking in enumerate(rankings):
            for rank, doc in enumerate(ranking, start=1):
                doc_id = str(doc.get("id", doc.get("_id", "")))
                
                # Add to document scores
                doc_scores[doc_id]["id"] = doc_id
                doc_scores[doc_id]["source"] = doc.get("source", doc)
                doc_scores[doc_id]["rrf_score"] += 1.0 / (self.k + rank)
                
                # Track individual ranking
                doc_scores[doc_id][rank_field][f"rank_{ranking_idx}"] = rank
                
                # Add score if available
                if score_field in doc and doc.get(score_field):
                    doc_scores[doc_id][f"score_{ranking_idx}"] = doc[score_field]
                
                # Add highlights
                if "highlight" in doc:
                    doc_scores[doc_id]["highlight"] = doc["highlight"]
        
        # Sort by RRF score
        results = list(doc_scores.values())
        results.sort(key=lambda x: x["rrf_score"], reverse=True)
        
        return results
    
    def _add_rrf_scores(
        self,
        ranking: list[dict[str, Any]],
        weights: list[float],
        score_field: str,
    ) -> list[dict[str, Any]]:
        """Add RRF scores to a single ranking."""
        for rank, doc in enumerate(ranking, start=1):
            doc[score_field] = weights[0] * (1.0 / (self.k + rank))
        return ranking


class HybridScorer:
    """
    Hybrid scorer that combines multiple scoring methods.
    
    Supports:
    - Vector similarity scores (cosine similarity)
    - BM25 lexical scores
    - Popularity/reputation signals
    - Freshness/decay factors
    """
    
    def __init__(
        self,
        vector_weight: float = 0.4,
        lexical_weight: float = 0.4,
        popularity_weight: float = 0.1,
        freshness_weight: float = 0.1,
    ):
        """
        Initialize hybrid scorer.
        
        Args:
            vector_weight: Weight for vector similarity (0-1)
            lexical_weight: Weight for lexical/BM25 scores (0-1)
            popularity_weight: Weight for popularity signals (0-1)
            freshness_weight: Weight for recency/decay (0-1)
        """
        self.vector_weight = vector_weight
        self.lexical_weight = lexical_weight
        self.popularity_weight = popularity_weight
        self.freshness_weight = freshness_weight
        
        # Normalize weights
        total = vector_weight + lexical_weight + popularity_weight + freshness_weight
        if total > 0:
            self.vector_weight /= total
            self.lexical_weight /= total
            self.popularity_weight /= total
            self.freshness_weight /= total
    
    def combine_scores(
        self,
        results: list[dict[str, Any]],
        score_prefix: str = "score_",
    ) -> list[dict[str, Any]]:
        """
        Combine multiple scores into a final ranking.
        
        Args:
            results: List of results with individual scores
            score_prefix: Prefix for score fields
        
        Returns:
            Results with combined_score added
        """
        if not results:
            return []
        
        # Find all score components
        components = set()
        for doc in results:
            for key in doc.keys():
                if key.startswith(score_prefix):
                    components.add(key)
        
        # Calculate combined scores
        for doc in results:
            combined = 0.0
            
            if "vector_similarity" in doc:
                combined += self.vector_weight * doc["vector_similarity"]
            if f"{score_prefix}vector" in doc:
                combined += self.vector_weight * doc[f"{score_prefix}vector"]
            
            if "bm25_score" in doc:
                combined += self.lexical_weight * doc["bm25_score"]
            if f"{score_prefix}lexical" in doc:
                combined += self.lexical_weight * doc[f"{score_prefix}lexical"]
            if "_score" in doc:  # Elasticsearch default score
                combined += self.lexical_weight * self._normalize_elasticsearch_score(doc["_score"])
            
            if "popularity_score" in doc:
                combined += self.popularity_weight * doc["popularity_score"]
            
            if "recency_score" in doc:
                combined += self.freshness_weight * doc["recency_score"]
            
            doc["combined_score"] = combined
        
        # Sort by combined score
        results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        
        return results
    
    def _normalize_elasticsearch_score(self, score: float) -> float:
        """
        Normalize Elasticsearch scores to 0-1 range.
        
        Elasticsearch BM25 scores are unbounded, so we use a sigmoid-like
        transformation to compress extreme values.
        """
        # Simple normalization: log transform + min-max
        import math
        log_score = math.log1p(max(0, score))
        return min(1.0, log_score / 10.0)


class LearningToRankScorer:
    """
    Learning-to-Rank style scorer using feature combination.
    
    This is a simplified implementation that combines features
    with learned weights. In production, this could use a trained
    model (e.g., XGBoost, LightGBM) for better ranking.
    """
    
    def __init__(self, feature_weights: dict[str, float] | None = None):
        """
        Initialize LTR scorer.
        
        Args:
            feature_weights: Dict mapping feature names to weights
        """
        self.feature_weights = feature_weights or {
            "relevance": 0.35,
            "popularity": 0.25,
            "freshness": 0.20,
            "quality": 0.15,
            "completeness": 0.05,
        }
    
    def score(self, features: dict[str, float]) -> float:
        """
        Calculate weighted score from features.
        
        Args:
            features: Dict of feature values
        
        Returns:
            Combined score
        """
        score = 0.0
        for feature_name, weight in self.feature_weights.items():
            value = features.get(feature_name, 0.0)
            score += weight * value
        return score
    
    def rank(
        self,
        results: list[dict[str, Any]],
        feature_extractor: callable,
    ) -> list[dict[str, Any]]:
        """
        Rank results using extracted features.
        
        Args:
            results: List of search results
            feature_extractor: Function to extract features from a result
        
        Returns:
            Ranked results with scores
        """
        for result in results:
            features = feature_extractor(result)
            result["ltr_score"] = self.score(features)
        
        results.sort(key=lambda x: x.get("ltr_score", 0), reverse=True)
        return results


class BoostingReranker:
    """
    Reranker that applies contextual boosts.
    
    Boosts can be based on:
    - User context (preferences, history)
    - Content attributes (featured, premium)
    - Temporal factors (recent content)
    """
    
    def __init__(self):
        """Initialize boosting reranker."""
        self.boosts: list[dict[str, Any]] = []
    
    def add_boost(
        self,
        condition: callable,
        factor: float,
        description: str = "",
    ) -> "BoostingReranker":
        """
        Add a boost rule.
        
        Args:
            condition: Function that returns True if boost applies
            factor: Multiplicative factor (>1 boosts, <1 demotes)
            description: Human-readable description
        
        Returns:
            Self for chaining
        """
        self.boosts.append({
            "condition": condition,
            "factor": factor,
            "description": description,
        })
        return self
    
    def rerank(
        self,
        results: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Apply boosts and rerank.
        
        Args:
            results: Search results
            context: Optional context for conditional boosts
        
        Returns:
            Reranked results
        """
        context = context or {}
        
        for result in results:
            score = result.get("combined_score", result.get("_score", 1.0))
            
            for boost_rule in self.boosts:
                condition = boost_rule["condition"]
                factor = boost_rule["factor"]
                
                if condition(result, context):
                    score *= factor
                    logger.debug(
                        "boost_applied",
                        factor=factor,
                        description=boost_rule["description"],
                    )
            
            result["boosted_score"] = score
        
        results.sort(key=lambda x: x.get("boosted_score", 0), reverse=True)
        return results


def create_default_reranker() -> BoostingReranker:
    """Create a default reranker with common boosts."""
    reranker = BoostingReranker()
    
    # Boost featured content
    reranker.add_boost(
        condition=lambda r, c: r.get("source", {}).get("is_featured", False),
        factor=1.5,
        description="Featured content boost",
    )
    
    # Boost public content
    reranker.add_boost(
        condition=lambda r, c: r.get("source", {}).get("is_public", False),
        factor=1.2,
        description="Public content boost",
    )
    
    # Boost high-rated content
    reranker.add_boost(
        condition=lambda r, c: (
            r.get("source", {}).get("metadata_record", {}).get("average_rating", 0) or 0
        ) >= 4.0,
        factor=1.3,
        description="High rating boost",
    )
    
    return reranker
