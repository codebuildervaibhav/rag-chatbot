from typing import List, Tuple, Dict
from src.embeddings.mock_vertex import MockVertexEmbeddingModel
from src.storage.faiss_store import FAISSVectorStore

class RetrievalOrchestrator:
    def __init__(self, vector_store: FAISSVectorStore, embedder: MockVertexEmbeddingModel, expander):
        self.vector_store = vector_store
        self.embedder = embedder
        self.expander = expander

    def run_strategy_a(self, query: str) -> Dict:
        """Raw Vector Search."""
        vec = self.embedder.embed_text(query)
        results = self.vector_store.search(vec, top_k=3)
        return {"query": query, "results": results}

    def run_strategy_b(self, query: str) -> Dict:
        """AI-Enhanced Retrieval."""
        expanded_query = self.expander.expand(query)
        vec = self.embedder.embed_text(expanded_query)
        results = self.vector_store.search(vec, top_k=3)
        return {
            "query": query,
            "expanded_query": expanded_query,
            "results": results
        }
