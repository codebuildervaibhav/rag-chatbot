import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from src.embeddings.mock_vertex import MockVertexEmbeddingModel
from src.storage.faiss_store import FAISSVectorStore
from src.retrieval.query_expander import MockVertexExpander
from src.retrieval.orchestrator import RetrievalOrchestrator

@pytest.fixture
def mock_embedder():
    """Mocking the GCP SDK (Vertex AI) via our local sentence-transformers fallback."""
    return MockVertexEmbeddingModel()

@pytest.fixture
def vector_store(mock_embedder):
    return FAISSVectorStore(dimension=mock_embedder.dimension)

@pytest.fixture
def orchestrator(mock_embedder, vector_store):
    expander = MockVertexExpander()
    return RetrievalOrchestrator(vector_store, mock_embedder, expander)

def test_embedder_dimension(mock_embedder):
    """Test that the mocked Vertex AI embedder returns the expected 384-dimensional vector."""
    vec = mock_embedder.embed_text("test query")
    assert vec.shape == (384,)
    assert isinstance(vec, np.ndarray)

def test_faiss_insertion_and_search(vector_store, mock_embedder):
    """Test that vectors can be successfully ingested and retrieved from FAISS."""
    docs = ["Kubernetes uses HPA for autoscaling.", "Kafka is used as a message broker."]
    metadata = [{"id": "chunk_1", "content": docs[0]}, {"id": "chunk_2", "content": docs[1]}]
    
    vectors = mock_embedder.embed_batch(docs)
    vector_store.add_vectors(vectors, metadata)
    
    assert vector_store.index.ntotal == 2
    
    # Search for autoscaling
    query_vec = mock_embedder.embed_text("How does autoscaling work?")
    results = vector_store.search(query_vec, top_k=1)
    
    assert len(results) == 1
    assert results[0][0] == "chunk_1"
    assert "HPA" in results[0][2]["content"]

def test_query_expander_mock():
    """Test that the Query Expander correctly expands target mock queries."""
    expander = MockVertexExpander()
    query = "What is the procedure for the blue screen?"
    expanded = expander.expand(query)
    
    assert expanded != query
    assert "fault tolerance" in expanded.lower()
    
def test_orchestrator_strategies(orchestrator, mock_embedder, vector_store):
    """Test that Strategy A and Strategy B execute successfully."""
    # Seed data
    docs = ["Traffic spikes are handled by worker nodes.", "Fallback mechanisms exist for fault tolerance."]
    metadata = [{"id": "chunk_1", "content": docs[0]}, {"id": "chunk_2", "content": docs[1]}]
    vectors = mock_embedder.embed_batch(docs)
    vector_store.add_vectors(vectors, metadata)
    
    # Run Strategy A
    res_a = orchestrator.run_strategy_a("What is the fault tolerance mechanism?")
    assert "query" in res_a
    assert "results" in res_a
    assert len(res_a["results"]) > 0
    
    # Run Strategy B
    res_b = orchestrator.run_strategy_b("What is the procedure for the blue screen?")
    assert "expanded_query" in res_b
    assert "results" in res_b
    assert res_b["query"] != res_b["expanded_query"]
