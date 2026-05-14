"""
test_faiss_store.py — Verifies insert and search operations on the FAISS vector store.
Tests the VectorStore ABC implementation with IndexFlatIP (Cosine Similarity).
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from src.embeddings.mock_vertex import MockVertexEmbeddingModel
from src.storage.faiss_store import FAISSVectorStore


@pytest.fixture
def embedder():
    return MockVertexEmbeddingModel()


@pytest.fixture
def store(embedder):
    return FAISSVectorStore(dimension=embedder.dimension)


class TestFAISSVectorStore:
    """Tests for the FAISS VectorStore implementation."""

    def test_empty_store_has_zero_vectors(self, store):
        """A freshly created store must contain zero vectors."""
        assert store.index.ntotal == 0

    def test_insertion_increases_count(self, store, embedder):
        """Adding vectors must increase the index total."""
        docs = ["Kubernetes uses HPA for autoscaling.", "Kafka is a message broker."]
        metadata = [{"id": "chunk_1", "content": docs[0]}, {"id": "chunk_2", "content": docs[1]}]
        vectors = embedder.embed_batch(docs)
        store.add_vectors(vectors, metadata)
        assert store.index.ntotal == 2

    def test_search_returns_correct_chunk(self, store, embedder):
        """Searching for 'autoscaling' must return the chunk about HPA first."""
        docs = ["Kubernetes uses HPA for autoscaling.", "Kafka is a message broker."]
        metadata = [{"id": "chunk_1", "content": docs[0]}, {"id": "chunk_2", "content": docs[1]}]
        vectors = embedder.embed_batch(docs)
        store.add_vectors(vectors, metadata)

        query_vec = embedder.embed_text("How does autoscaling work?")
        results = store.search(query_vec, top_k=1)

        assert len(results) == 1
        assert results[0][0] == "chunk_1"
        assert "HPA" in results[0][2]["content"]

    def test_search_returns_scores(self, store, embedder):
        """Search results must include a float similarity score."""
        docs = ["Test document about machine learning."]
        metadata = [{"id": "doc_1", "content": docs[0]}]
        vectors = embedder.embed_batch(docs)
        store.add_vectors(vectors, metadata)

        query_vec = embedder.embed_text("machine learning")
        results = store.search(query_vec, top_k=1)

        assert isinstance(results[0][1], float)

    def test_top_k_limits_results(self, store, embedder):
        """top_k=1 must return exactly 1 result even if more vectors exist."""
        docs = ["Doc A", "Doc B", "Doc C"]
        metadata = [{"id": f"d_{i}", "content": d} for i, d in enumerate(docs)]
        vectors = embedder.embed_batch(docs)
        store.add_vectors(vectors, metadata)

        query_vec = embedder.embed_text("Doc")
        results = store.search(query_vec, top_k=1)
        assert len(results) == 1
