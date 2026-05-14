import faiss
import numpy as np
from typing import List, Tuple
from .base import VectorStore

class FAISSVectorStore(VectorStore):
    """
    FAISS implementation using IndexFlatIP. 
    By L2-normalizing vectors before insertion and searching, 
    Inner Product mathematically equates to Cosine Similarity.
    """
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.documents: List[dict] = []

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """L2 normalizes vectors to enable exact Cosine Similarity search."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1 # Prevent division by zero
        return vectors / norms

    def add_vectors(self, vectors: np.ndarray, metadata: List[dict]) -> None:
        normalized = self._normalize(vectors.astype(np.float32))
        self.index.add(normalized)
        self.documents.extend(metadata)

    def search(self, query_vector: np.ndarray, top_k: int = 3) -> List[Tuple[str, float, dict]]:
        if self.index.ntotal == 0:
            return []
            
        query_normalized = self._normalize(query_vector.reshape(1, -1).astype(np.float32))
        scores, indices = self.index.search(query_normalized, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.documents):
                results.append((
                    self.documents[idx].get("id", str(idx)),
                    float(score),
                    self.documents[idx]
                ))
        return results
