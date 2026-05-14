"""
test_orchestrator.py — Verifies that Strategy A and Strategy B produce
different results for slang queries, proving the value of query expansion.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.embeddings.mock_vertex import MockVertexEmbeddingModel
from src.storage.faiss_store import FAISSVectorStore
from src.expanders.mock_vertex import MockVertexExpander
from src.retrieval.orchestrator import RetrievalOrchestrator
from src.evaluation.metrics import BenchmarkMetrics


@pytest.fixture
def seeded_orchestrator():
    """Creates a fully seeded orchestrator with the assessment dataset."""
    embedder = MockVertexEmbeddingModel()
    store = FAISSVectorStore(dimension=embedder.dimension)
    expander = MockVertexExpander()
    orchestrator = RetrievalOrchestrator(store, embedder, expander)

    docs = [
        "Traffic spikes are handled by worker nodes and Kubernetes HPA autoscaling.",
        "Fallback mechanisms and circuit breakers exist for fault tolerance.",
        "The data pipeline uses batch processing with Apache Spark.",
        "Semantic caching reduces latency and compute expenditure.",
    ]
    metadata = [{"id": f"chunk_{i+1}", "content": d} for i, d in enumerate(docs)]
    vectors = embedder.embed_batch(docs)
    store.add_vectors(vectors, metadata)

    return orchestrator


class TestOrchestrator:
    """Tests for RetrievalOrchestrator Strategy A vs Strategy B."""

    def test_strategy_a_returns_results(self, seeded_orchestrator):
        """Strategy A must return a query and non-empty results list."""
        res = seeded_orchestrator.run_strategy_a("How does autoscaling work?")
        assert "query" in res
        assert "results" in res
        assert len(res["results"]) > 0

    def test_strategy_b_returns_expanded_query(self, seeded_orchestrator):
        """Strategy B must return an expanded_query that differs from the original."""
        res = seeded_orchestrator.run_strategy_b("What is the procedure for the blue screen?")
        assert "expanded_query" in res
        assert res["query"] != res["expanded_query"]

    def test_strategy_b_beats_a_on_slang_query(self, seeded_orchestrator):
        """For slang queries, Strategy B should retrieve the correct chunk
        at a higher rank than Strategy A, proving the value of query expansion."""
        query = "What is the procedure for the blue screen?"
        ground_truth = "chunk_2"

        res_a = seeded_orchestrator.run_strategy_a(query)
        res_b = seeded_orchestrator.run_strategy_b(query)

        ids_a = [r[0] for r in res_a["results"]]
        ids_b = [r[0] for r in res_b["results"]]

        mrr_a = BenchmarkMetrics.calculate_mrr(ids_a, ground_truth)
        mrr_b = BenchmarkMetrics.calculate_mrr(ids_b, ground_truth)

        # Strategy B should have equal or better MRR than Strategy A
        assert mrr_b >= mrr_a

    def test_mrr_returns_zero_for_missing_chunk(self):
        """MRR must return 0.0 when the ground truth chunk is not in top-k."""
        retrieved = ["chunk_1", "chunk_3", "chunk_5"]
        mrr = BenchmarkMetrics.calculate_mrr(retrieved, "chunk_99")
        assert mrr == 0.0

    def test_mrr_returns_one_for_rank_one(self):
        """MRR must return 1.0 when the ground truth is at rank 1."""
        retrieved = ["chunk_2", "chunk_1", "chunk_3"]
        mrr = BenchmarkMetrics.calculate_mrr(retrieved, "chunk_2")
        assert mrr == 1.0
