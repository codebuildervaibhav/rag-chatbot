from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

class VectorStore(ABC):
    """Interface for vector storage and retrieval."""
    
    @abstractmethod
    def add_vectors(self, vectors: np.ndarray, metadata: List[dict]) -> None:
        pass
    
    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int = 3) -> List[Tuple[str, float, dict]]:
        pass
