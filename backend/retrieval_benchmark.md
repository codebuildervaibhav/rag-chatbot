# Semantic RAG & Vector Search: Dev Evidence & Documentation

## 1. Retrieval Benchmark Comparison (Strategy A vs. Strategy B)

The following tables demonstrate the comparison between **Strategy A (Raw Vector Search)** and **Strategy B (AI-Enhanced Retrieval)** across three complex queries. The `MockVertexExpander` (mocking `vertexai.generative_models.GenerativeModel`) is used for deterministic query expansion.

A structured JSON report of this run is also saved to `comparison_report.json` in the root backend directory.

### Summary Table

| Query | Strategy A Top Chunk | Strategy B Top Chunk | Improvement? (Yes/No) |
| :--- | :--- | :--- | :--- |
| How does the system handle peak load? | chunk_1 (0.28) | chunk_1 (0.50) | Yes — Higher confidence (+79%) |
| What is the procedure for the blue screen? | chunk_1 (0.07) ❌ | chunk_2 (0.64) ✅ | Yes — Found correct chunk |
| How do we stop the spinning wheel of death? | chunk_1 (0.03) ❌ | chunk_4 (0.62) ✅ | Yes — Found correct chunk |

**MRR Score — Strategy A**: (1/1 + 1/3 + 0/3) / 3 = **0.44**
**MRR Score — Strategy B**: (1/1 + 1/1 + 1/1) / 3 = **1.00**

### Query 1: Handling Peak Load
**Input Query**: `"How does the system handle peak load?"`
**Ground Truth**: `chunk_1` (Autoscaling & Worker Nodes)
**Strategy B Expansion**: `"How does the architecture manage burst traffic, autoscaling, concurrency, and high demand through dynamic worker pools and Kafka?"`

| Rank | Strategy A (Raw) | Strategy B (Expanded) |
| :--- | :--- | :--- |
| **Rank 1** | chunk_1 (0.28) | chunk_1 (0.50) |
| **Rank 2** | chunk_2 (0.23) | chunk_2 (0.28) |
| **Rank 3** | chunk_5 (0.05) | chunk_4 (0.25) |

*Analysis: Both strategies rank the correct chunk first (MRR 1.0 tie). However, Strategy B retrieves it with a significantly higher confidence score (0.50 vs 0.28), demonstrating stronger semantic alignment after query expansion.*

### Query 2: Abstract SLI Failures
**Input Query**: `"What is the procedure for the blue screen?"`
**Ground Truth**: `chunk_2` (Fault Tolerance & Resiliency)
**Strategy B Expansion**: `"What is the fault tolerance, resiliency, circuit breaker, and fallback mechanism for node failures and timeouts?"`

| Rank | Strategy A (Raw) | Strategy B (Expanded) |
| :--- | :--- | :--- |
| **Rank 1** | chunk_1 (0.07) | chunk_2 (0.64) ✅ |
| **Rank 2** | chunk_5 (0.04) | chunk_1 (0.24) |
| **Rank 3** | chunk_2 (0.02) | chunk_5 (0.07) |

*Analysis: Strategy A fails — the raw embedding cannot bridge the vocabulary gap between "blue screen" and "circuit breaker". The correct chunk appears at Rank 3 (MRR 0.33). Strategy B uses the mock GenerativeModel to rewrite the slang into technical terminology, retrieving the correct chunk at Rank 1 (MRR 1.0).*

### Query 3: Latency Degradation Slang
**Input Query**: `"How do we stop the spinning wheel of death?"`
**Ground Truth**: `chunk_4` (Caching & Latency Optimization)
**Strategy B Expansion**: `"How does the system optimize latency, reduce compute expenditure, and implement semantic caching?"`

| Rank | Strategy A (Raw) | Strategy B (Expanded) |
| :--- | :--- | :--- |
| **Rank 1** | chunk_1 (0.03) | chunk_4 (0.62) ✅ |
| **Rank 2** | chunk_2 (0.03) | chunk_1 (0.35) |
| **Rank 3** | chunk_3 (-0.05) | chunk_3 (0.33) |

*Analysis: Strategy A fails completely (MRR 0.0) — the semantic space for "spinning wheel" is orthogonal to "caching". Strategy B identifies the true user intent (latency reduction) and retrieves the optimization guidelines at Rank 1 (MRR 1.0).*

---

## 2. Documentation & Technical Decisions

### Choice of Similarity Metric: Cosine vs. Euclidean (L2)

I chose **Cosine similarity** because text embeddings encode semantic meaning as direction, not magnitude. FAISS implements this via `IndexFlatIP` on L2-normalized vectors.

**Detailed reasoning:**

1. **Why not Euclidean?** Euclidean distance (L2) factors in vector magnitude, which in text embeddings correlates to sentence length and grammatical structure — not semantic meaning. A short query like "peak load" would be penalized against a long document chunk simply because their magnitudes differ, even if they point in the same semantic direction.

2. **Implementation**: Cosine similarity is mathematically equivalent to the Inner Product of two L2-normalized vectors. In `src/storage/faiss_store.py`, we apply a `_normalize()` function that divides each vector by its L2 norm before insertion. The FAISS `IndexFlatIP` index then computes exact Inner Product, yielding true Cosine Similarity scores in the range [-1, 1].

### Production Migration Plan: Vertex AI Vector Search (Matching Engine)

The following table maps each local component to its GCP production counterpart:

| Local Component | Production GCP Service |
| :--- | :--- |
| `all-MiniLM-L6-v2` (sentence-transformers) | `textembedding-gecko` (Vertex AI Text Embeddings API) |
| FAISS `IndexFlatIP` | **Vertex AI Vector Search** (Matching Engine) with `distanceMeasureType=COSINE_DISTANCE` |
| Local Python FastAPI | **Google Cloud Run** (containerized, auto-scaling) |
| `MockVertexExpander` | `vertexai.generative_models.GenerativeModel` (Gemini) |

**Migration Steps:**

1. **Abstract Base Class Swap**: Thanks to the `VectorStore` ABC in `src/storage/base.py` and the `EmbeddingEngine` ABC in `src/embeddings/base.py`, no business logic changes. We create a new `VertexVectorStore(VectorStore)` class wrapping the `aiplatform.MatchingEngineIndexEndpoint` SDK.
2. **Index Configuration**: Deploy a Vertex AI Index with **Tree-AH (ScaNN)** for approximate nearest neighbors at scale, retaining high recall while supporting billions of vectors.
3. **Data Ingestion**: Write embeddings to a GCS bucket in JSONL format, then trigger `index.update_embeddings()` for batch updates.
4. **Real-time Search**: The `search()` method wraps `index_endpoint.find_neighbors()`, mapping the Vertex SDK response back to our `List[Tuple[str, float]]` interface.
