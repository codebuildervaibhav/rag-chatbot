from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from .base import EmbeddingEngine

class MockVertexEmbeddingModel(EmbeddingEngine):
    """
    Simulates vertexai.language_models.TextEmbeddingModel behavior locally.
    Uses sentence-transformers to generate dense vectors.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # This simulates the textembedding-gecko dense vector generation
        self.model = SentenceTransformer(model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> np.ndarray:
        return self.model.encode([text])[0]

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts)

    @property
    def dimension(self) -> int:
        return self._dimension
