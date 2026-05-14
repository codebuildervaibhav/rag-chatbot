from abc import ABC, abstractmethod
from typing import List
import numpy as np

class EmbeddingEngine(ABC):
    """Interface for embedding generation to allow easy GCP migration."""
    
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        pass
