"""
test_mock_vertex.py — Verifies MockVertexExpander returns expected expansions
and MockVertexEmbeddingModel produces correct vector dimensions.
Mocking the GCP SDK: vertexai.language_models.TextEmbeddingModel
                     vertexai.generative_models.GenerativeModel
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from src.embeddings.mock_vertex import MockVertexEmbeddingModel
from src.expanders.mock_vertex import MockVertexExpander


class TestMockVertexEmbeddingModel:
    """Tests for the mocked vertexai.language_models.TextEmbeddingModel."""

    def test_embedding_dimension(self):
        """Embedding vectors must be 384-dimensional (all-MiniLM-L6-v2)."""
        embedder = MockVertexEmbeddingModel()
        vec = embedder.embed_text("test query")
        assert vec.shape == (384,)
        assert isinstance(vec, np.ndarray)

    def test_batch_embedding(self):
        """Batch embedding should return one vector per input string."""
        embedder = MockVertexEmbeddingModel()
        vecs = embedder.embed_batch(["hello", "world", "test"])
        assert vecs.shape == (3, 384)

    def test_different_texts_produce_different_vectors(self):
        """Semantically different texts should not produce identical vectors."""
        embedder = MockVertexEmbeddingModel()
        v1 = embedder.embed_text("Kubernetes autoscaling")
        v2 = embedder.embed_text("Chocolate cake recipe")
        assert not np.allclose(v1, v2)


class TestMockVertexExpander:
    """Tests for the mocked vertexai.generative_models.GenerativeModel."""

    def test_known_query_expansion(self):
        """Known assessment queries must return their deterministic expansion."""
        expander = MockVertexExpander()
        expanded = expander.expand("How does the system handle peak load?")
        assert "autoscaling" in expanded.lower()
        assert "Kafka" in expanded

    def test_blue_screen_expansion(self):
        """'Blue screen' slang must be expanded to fault tolerance terminology."""
        expander = MockVertexExpander()
        expanded = expander.expand("What is the procedure for the blue screen?")
        assert expanded != "What is the procedure for the blue screen?"
        assert "fault tolerance" in expanded.lower()

    def test_spinning_wheel_expansion(self):
        """'Spinning wheel' slang must be expanded to latency/caching terminology."""
        expander = MockVertexExpander()
        expanded = expander.expand("How do we stop the spinning wheel of death?")
        assert "latency" in expanded.lower()
        assert "caching" in expanded.lower()

    def test_unknown_query_fallback(self):
        """Unknown queries should return a graceful fallback, not raise an error."""
        expander = MockVertexExpander()
        expanded = expander.expand("Some completely unknown query")
        assert "Some completely unknown query" in expanded
