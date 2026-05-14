# Semantic RAG & Vector Search: Dev Evidence & Documentation

## 1. Retrieval Benchmark Comparison (Strategy A vs. Strategy B)

The following tables demonstrate the comparison between **Strategy A (Raw Vector Search)** and **Strategy B (AI-Enhanced Retrieval)** across three complex queries.

A structured JSON report of this run is also saved to `comparison_report.json` in the root backend directory.

### Query 1: Handling Peak Load
**Input Query**: `"How does the system handle peak load?"`
**Ground Truth**: `chunk_1` (Autoscaling & Worker Nodes)
**Strategy B Expansion**: `"How does the architecture manage burst traffic, autoscaling, concurrency, and high demand through dynamic worker pools and Kafka?"`

| Rank | Strategy A (Raw) | Strategy B (Expanded) |
| :--- | :--- | :--- |
| **Rank 1** | chunk_1 (0.28) | chunk_1 (0.50) |
| **Rank 2** | chunk_2 (0.23) | chunk_2 (0.28) |
| **Rank 3** | chunk_5 (0.05) | chunk_4 (0.25) |

*Analysis: Because the raw embedding model (`all-MiniLM-L6-v2`) is highly capable, it successfully linked "peak load" to "burst traffic" in chunk 1, resulting in a tie (MRR 1.0 for both). However, Strategy B retrieved the correct chunk with a significantly higher confidence score (0.50 vs 0.28).*

### Query 2: Abstract SLI Failures
**Input Query**: `"What is the procedure for the blue screen?"`
**Ground Truth**: `chunk_2` (Fault Tolerance & Resiliency)
**Strategy B Expansion**: `"What is the fault tolerance, resiliency, circuit breaker, and fallback mechanism for node failures and timeouts?"`

| Rank | Strategy A (Raw) | Strategy B (Expanded) |
| :--- | :--- | :--- |
| **Rank 1** | chunk_1 (0.07) | chunk_2 (0.64) |
| **Rank 2** | chunk_5 (0.04) | chunk_1 (0.24) |
| **Rank 3** | chunk_2 (0.02) | chunk_5 (0.07) |

*Analysis: The raw embedding struggles with domain-specific abstract slang ("blue screen" mapping to "server fault"). Strategy A retrieved the wrong chunks, barely catching the target at Rank 3 (MRR 0.33). Strategy B uses the LLM to rewrite the slang into technical terminology ("circuit breaker", "fallback"), perfectly retrieving the correct chunk at Rank 1 (MRR 1.0).*

### Query 3: Latency Degradation Slang
**Input Query**: `"How do we stop the spinning wheel of death?"`
**Ground Truth**: `chunk_4` (Caching & Latency Optimization)
**Strategy B Expansion**: `"How does the system optimize latency, reduce compute expenditure, and implement semantic caching?"`

| Rank | Strategy A (Raw) | Strategy B (Expanded) |
| :--- | :--- | :--- |
| **Rank 1** | chunk_1 (0.03) | chunk_4 (0.62) |
| **Rank 2** | chunk_2 (0.03) | chunk_1 (0.35) |
| **Rank 3** | chunk_3 (-0.05) | chunk_3 (0.33) |

*Analysis: Strategy A fails completely (MRR 0.0) as the semantic space for "spinning wheel" is orthogonal to "caching". Strategy B identifies the true user intent (latency reduction) and flawlessly retrieves the optimization guidelines (MRR 1.0).*

---

## 2. Documentation & Technical Decisions

### Choice of Similarity Metric: Cosine vs. Euclidean (L2)

For this assessment, **Cosine Similarity** is the superior choice and was implemented via mathematically equivalent techniques in FAISS.

1. **Why Cosine?**: In text embeddings, the *magnitude* of the vector generally correlates to the length or grammatical structure of the text, while the *direction* represents the semantic meaning. Because we only care about the semantic relevance between a short query and a longer document chunk, we want to isolate the directionality. Euclidean distance ($L_2$) factors in vector magnitude, which can penalize semantically similar texts that differ in length.
2. **Implementation via FAISS `IndexFlatIP`**: Cosine similarity is mathematically defined as the Inner Product of two vectors that have been $L_2$-normalized. In `backend/src/storage/faiss_store.py`, we implemented a `_normalize` function that divides vectors by their $L_2$ norm before feeding them into FAISS's `IndexFlatIP` (Inner Product). This achieves exact Cosine Similarity while keeping the FAISS index highly efficient.

### Migration Plan: Vertex AI Vector Search (Matching Engine)

While local FAISS is excellent for testing, production scale requires GCP's **Vertex AI Vector Search** (formerly Matching Engine) for high availability, billions of vectors, and sub-millisecond latencies.

**Production Migration Steps:**

1. **Abstract Base Class Swap**: 
   - Thanks to the `VectorStore` ABC design in `src/storage/base.py`, no business logic needs to change. We simply create a new `VertexVectorStore(VectorStore)` class that initializes the `aiplatform.MatchingEngineIndexEndpoint` from the GCP SDK.
2. **Index Configuration**: 
   - We will deploy a Vertex AI Index configured with `distanceMeasureType=COSINE_DISTANCE`.
   - For scale, we will configure the index to use **Tree-AH (ScaNN)** (Scalable Nearest Neighbors) rather than exhaustive exact search (brute force), allowing it to scale massively while retaining high recall.
3. **Data Ingestion**: 
   - Instead of inserting vectors locally, the ingestion pipeline will write the generated embeddings (from Vertex TextEmbeddings) and metadata to a Google Cloud Storage (GCS) bucket in JSONL format. 
   - We will then trigger a batch update to the Vertex AI Index via `index.update_embeddings()`.
4. **Real-time Search Integration**: 
   - The `search()` method in our new `VertexVectorStore` will simply wrap `index_endpoint.find_neighbors()`, mapping the Vertex SDK response back to our expected `List[Tuple[str, float, dict]]` format.
