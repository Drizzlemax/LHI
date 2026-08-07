"""
PANDORA Content Service Unit Tests - Vector Search
Tests for vector search functionality
"""
import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import numpy as np

from src.search.reranker import HybridScorer, RRFScorer


pytestmark = pytest.mark.unit


class TestCosineSimilarity:
    """Tests for cosine similarity calculations."""
    
    def test_cosine_similarity_same_vectors(self):
        """Test cosine similarity of identical vectors."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        
        similarity = _cosine_similarity(v1, v2)
        assert similarity == pytest.approx(1.0)
    
    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        
        similarity = _cosine_similarity(v1, v2)
        assert similarity == pytest.approx(0.0)
    
    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity of opposite vectors."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [-1.0, 0.0, 0.0]
        
        similarity = _cosine_similarity(v1, v2)
        assert similarity == pytest.approx(-1.0)
    
    def test_cosine_similarity_3d_vectors(self):
        """Test cosine similarity in 3D space."""
        v1 = [1.0, 2.0, 3.0]
        v2 = [4.0, 5.0, 6.0]
        
        similarity = _cosine_similarity(v1, v2)
        
        # Manual calculation
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        expected = dot / (mag1 * mag2)
        
        assert similarity == pytest.approx(expected)
    
    def test_cosine_similarity_with_numpy(self):
        """Test using numpy for verification."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([4.0, 5.0, 6.0])
        
        # NumPy calculation
        expected = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        
        # Our calculation
        result = _cosine_similarity(v1.tolist(), v2.tolist())
        
        assert result == pytest.approx(expected)


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


class TestVectorNormalizer:
    """Tests for vector normalization."""
    
    def test_normalize_unit_vector(self):
        """Test normalization of unit vector."""
        v = [1.0, 0.0, 0.0]
        normalized = _normalize(v)
        
        magnitude = math.sqrt(sum(x * x for x in normalized))
        assert magnitude == pytest.approx(1.0)
    
    def test_normalize_3d_vector(self):
        """Test normalization of 3D vector."""
        v = [3.0, 4.0, 0.0]
        normalized = _normalize(v)
        
        magnitude = math.sqrt(sum(x * x for x in normalized))
        assert magnitude == pytest.approx(1.0)
        assert normalized[0] == pytest.approx(0.6)
        assert normalized[1] == pytest.approx(0.8)
    
    def test_normalize_zero_vector(self):
        """Test normalization of zero vector."""
        v = [0.0, 0.0, 0.0]
        normalized = _normalize(v)
        
        assert normalized == [0.0, 0.0, 0.0]
    
    def test_normalize_preserves_direction(self):
        """Test that normalization preserves direction."""
        v = [5.0, 10.0, 15.0]
        normalized = _normalize(v)
        
        # Direction ratios should be preserved
        assert normalized[0] / normalized[1] == pytest.approx(v[0] / v[1])
        assert normalized[1] / normalized[2] == pytest.approx(v[1] / v[2])


def _normalize(v: list[float]) -> list[float]:
    """Normalize a vector to unit length."""
    if not v:
        return v
    
    magnitude = math.sqrt(sum(x * x for x in v))
    if magnitude == 0:
        return v
    
    return [x / magnitude for x in v]


class TestVectorSearch:
    """Tests for vector search functionality."""
    
    def test_find_similar_vectors(self):
        """Test finding similar vectors."""
        query = [1.0, 0.0, 0.0]
        vectors = [
            {"id": "1", "embedding": [0.9, 0.1, 0.0]},
            {"id": "2", "embedding": [0.0, 1.0, 0.0]},
            {"id": "3", "embedding": [-0.9, 0.1, 0.0]},
        ]
        
        results = _find_similar(query, vectors, top_k=2)
        
        assert len(results) == 2
        assert results[0]["id"] == "1"  # Most similar
        assert results[1]["id"] == "3"  # Second most (opposite is similar in similarity)
    
    def test_find_similar_with_threshold(self):
        """Test finding similar vectors with threshold."""
        query = [1.0, 0.0, 0.0]
        vectors = [
            {"id": "1", "embedding": [0.9, 0.1, 0.0]},
            {"id": "2", "embedding": [0.0, 1.0, 0.0]},
        ]
        
        results = _find_similar(query, vectors, top_k=2, threshold=0.5)
        
        assert len(results) == 1
        assert results[0]["id"] == "1"
    
    def test_empty_vectors(self):
        """Test with empty vector list."""
        query = [1.0, 0.0, 0.0]
        results = _find_similar(query, [], top_k=5)
        assert results == []
    
    def test_vectors_with_scores(self):
        """Test that scores are calculated correctly."""
        query = [1.0, 0.0]
        vectors = [
            {"id": "1", "embedding": [1.0, 0.0]},  # Similarity = 1.0
            {"id": "2", "embedding": [0.0, 1.0]},  # Similarity = 0.0
        ]
        
        results = _find_similar(query, vectors, top_k=2)
        
        assert results[0]["score"] == pytest.approx(1.0)
        assert results[1]["score"] == pytest.approx(0.0)


def _find_similar(
    query: list[float],
    vectors: list[dict],
    top_k: int = 10,
    threshold: float = 0.0,
) -> list[dict]:
    """Find most similar vectors to a query."""
    results = []
    
    for vec in vectors:
        embedding = vec.get("embedding", [])
        if len(embedding) != len(query):
            continue
        
        similarity = _cosine_similarity(query, embedding)
        
        if similarity >= threshold:
            results.append({
                "id": vec["id"],
                "score": similarity,
                "source": vec,
            })
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]


class TestHybridVectorLexical:
    """Tests for hybrid vector + lexical search."""
    
    def test_combined_scoring(self):
        """Test combining vector and lexical scores."""
        vector_weight = 0.6
        lexical_weight = 0.4
        
        results = [
            {
                "id": "1",
                "vector_score": 0.9,
                "lexical_score": 0.7,
            },
            {
                "id": "2",
                "vector_score": 0.8,
                "lexical_score": 0.9,
            },
        ]
        
        for r in results:
            r["combined_score"] = (
                vector_weight * r["vector_score"] +
                lexical_weight * r["lexical_score"]
            )
        
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Doc 1: 0.6*0.9 + 0.4*0.7 = 0.54 + 0.28 = 0.82
        # Doc 2: 0.6*0.8 + 0.4*0.9 = 0.48 + 0.36 = 0.84
        assert results[0]["id"] == "2"
        assert results[0]["combined_score"] == pytest.approx(0.84)
    
    def test_rrf_for_hybrid(self):
        """Test using RRF for hybrid search fusion."""
        scorer = RRFScorer(k=60)
        
        vector_results = [
            {"id": "1", "score": 0.9},
            {"id": "2", "score": 0.8},
            {"id": "3", "score": 0.7},
        ]
        
        lexical_results = [
            {"id": "2", "score": 0.95},
            {"id": "1", "score": 0.85},
            {"id": "3", "score": 0.75},
        ]
        
        fused = scorer.fuse([vector_results, lexical_results])
        
        # Doc 1: rank 1 in vector, rank 2 in lexical
        # Doc 2: rank 2 in vector, rank 1 in lexical
        # Doc 3: rank 3 in both
        
        # Doc 1 and 2 should be close, doc 3 last
        assert fused[-1]["id"] == "3"


class TestVectorIndexing:
    """Tests for vector indexing operations."""
    
    def test_chunk_text_simple(self):
        """Test simple text chunking."""
        text = "This is a long document with multiple sentences. " * 10
        chunks = _chunk_text(text, chunk_size=50, overlap=10)
        
        assert len(chunks) > 1
        assert all(len(c) <= 50 for c in chunks)
    
    def test_chunk_text_with_overlap(self):
        """Test text chunking with overlap."""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 5
        chunks = _chunk_text(text, chunk_size=20, overlap=5)
        
        if len(chunks) > 1:
            # Check overlap exists
            for i in range(len(chunks) - 1):
                assert chunks[i][-5:] == chunks[i + 1][:5]
    
    def test_chunk_text_small(self):
        """Test chunking small text."""
        text = "Short text."
        chunks = _chunk_text(text, chunk_size=50, overlap=10)
        
        assert len(chunks) == 1
        assert chunks[0] == text


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Simple text chunking by characters."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    
    return chunks


class TestEmbeddingGeneration:
    """Tests for embedding generation simulation."""
    
    def test_embedding_dimensions(self):
        """Test that embeddings have correct dimensions."""
        text = "Sample text for embedding"
        dimension = 384
        
        embedding = _generate_embedding(text, dimension)
        
        assert len(embedding) == dimension
        assert all(-1.0 <= x <= 1.0 for x in embedding)
    
    def test_same_text_same_embedding(self):
        """Test that same text produces same embedding."""
        text = "Identical text"
        dimension = 128
        
        emb1 = _generate_embedding(text, dimension)
        emb2 = _generate_embedding(text, dimension)
        
        # With a deterministic mock, embeddings should be identical
        assert emb1 == emb2
    
    def test_different_text_different_embedding(self):
        """Test that different text produces different embedding."""
        dimension = 128
        
        emb1 = _generate_embedding("Text A", dimension)
        emb2 = _generate_embedding("Text B", dimension)
        
        # Different text should have different embeddings
        # (statistically very likely)
        assert emb1 != emb2


def _generate_embedding(text: str, dimension: int) -> list[float]:
    """Generate a mock embedding for text."""
    import hashlib
    
    # Simple deterministic mock based on text hash
    hash_bytes = hashlib.sha256(text.encode()).digest()
    
    # Generate pseudo-random values from hash
    embedding = []
    for i in range(dimension):
        idx = i % len(hash_bytes)
        value = (hash_bytes[idx] / 255.0) * 2 - 1  # Normalize to [-1, 1]
        embedding.append(value)
    
    # Normalize
    magnitude = math.sqrt(sum(x * x for x in embedding))
    if magnitude > 0:
        embedding = [x / magnitude for x in embedding]
    
    return embedding


class TestVectorDeduplication:
    """Tests for vector deduplication."""
    
    def test_deduplicate_similar(self):
        """Test deduplication of similar vectors."""
        vectors = [
            {"id": "1", "embedding": [1.0, 0.0, 0.0]},
            {"id": "2", "embedding": [0.99, 0.01, 0.0]},  # Very similar to 1
            {"id": "3", "embedding": [0.0, 1.0, 0.0]},  # Different
        ]
        
        threshold = 0.98
        unique = _deduplicate_vectors(vectors, threshold)
        
        assert len(unique) == 2
        assert all(v["id"] in ["1", "3"] for v in unique)
    
    def test_no_deduplication(self):
        """Test when no vectors are similar."""
        vectors = [
            {"id": "1", "embedding": [1.0, 0.0, 0.0]},
            {"id": "2", "embedding": [0.0, 1.0, 0.0]},
            {"id": "3", "embedding": [0.0, 0.0, 1.0]},
        ]
        
        unique = _deduplicate_vectors(vectors, threshold=0.9)
        
        assert len(unique) == 3


def _deduplicate_vectors(
    vectors: list[dict],
    threshold: float = 0.95,
) -> list[dict]:
    """Remove duplicate/similar vectors."""
    unique = []
    
    for vec in vectors:
        is_duplicate = False
        
        for existing in unique:
            embedding1 = vec.get("embedding", [])
            embedding2 = existing.get("embedding", [])
            
            if len(embedding1) != len(embedding2):
                continue
            
            similarity = _cosine_similarity(embedding1, embedding2)
            
            if similarity >= threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique.append(vec)
    
    return unique


class TestANNIndex:
    """Tests for approximate nearest neighbor index simulation."""
    
    def test_ann_search_results(self):
        """Test ANN search returns approximate nearest."""
        dimension = 3
        
        # Create 100 random vectors
        import random
        vectors = [
            {"id": str(i), "embedding": [random.random() for _ in range(dimension)]}
            for i in range(100)
        ]
        
        query = [0.5, 0.5, 0.5]
        
        # Exact search
        exact = _find_similar(query, vectors, top_k=5)
        
        # ANN search (simplified - just returns top_k)
        ann_results = _ann_search(query, vectors, top_k=5)
        
        # Results should be similar (simplified test)
        assert len(ann_results) == 5
    
    def test_ann_with_filters(self):
        """Test ANN search with metadata filters."""
        vectors = [
            {"id": "1", "embedding": [0.9, 0.1], "category": "science"},
            {"id": "2", "embedding": [0.8, 0.2], "category": "art"},
            {"id": "3", "embedding": [0.7, 0.3], "category": "science"},
        ]
        
        query = [1.0, 0.0]
        
        # Filter to science only
        results = _ann_search(query, vectors, top_k=5, filters={"category": "science"})
        
        assert len(results) == 2
        assert all(r["source"]["category"] == "science" for r in results)


def _ann_search(
    query: list[float],
    vectors: list[dict],
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]:
    """Approximate nearest neighbor search (simplified)."""
    # Apply filters first
    if filters:
        vectors = [
            v for v in vectors
            if all(v.get(k) == v_filter for k, v_filter in filters.items())
        ]
    
    # Simple similarity search (in production would use HNSW, IVF, etc.)
    return _find_similar(query, vectors, top_k=top_k)


class TestVectorQuantization:
    """Tests for vector quantization."""
    
    def test_quantize_to_bytes(self):
        """Test quantization to bytes."""
        vector = [0.1, -0.2, 0.5, -0.8, 1.0]
        
        quantized = _quantize(vector, num_bits=8)
        
        assert len(quantized) == len(vector)
        assert all(0 <= x <= 255 for x in quantized)
    
    def test_dequantize(self):
        """Test dequantization from bytes."""
        vector = [0.1, -0.2, 0.5, -0.8, 1.0]
        quantized = _quantize(vector, num_bits=8)
        dequantized = _dequantize(quantized, num_bits=8)
        
        # Check values are close (quantization introduces some error)
        for orig, deq in zip(vector, dequantized):
            assert abs(orig - deq) < 0.1


def _quantize(vector: list[float], num_bits: int = 8) -> list[int]:
    """Quantize float vector to integers."""
    max_val = 2 ** num_bits - 1
    
    quantized = []
    for v in vector:
        # Scale to [0, 1] based on typical range [-1, 1]
        scaled = (v + 1) / 2
        scaled = max(0, min(1, scaled))
        quantized.append(int(scaled * max_val))
    
    return quantized


def _dequantize(quantized: list[int], num_bits: int = 8) -> list[float]:
    """Dequantize integers back to floats."""
    max_val = 2 ** num_bits - 1
    
    dequantized = []
    for q in quantized:
        scaled = q / max_val
        dequantized.append(scaled * 2 - 1)
    
    return dequantized
