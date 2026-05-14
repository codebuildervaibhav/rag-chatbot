from dataclasses import dataclass
from typing import List

@dataclass
class Document:
    id: str
    content: str
    metadata: dict

class DatasetLoader:
    """Abstracts document ingestion to support multiple formats in the future."""
    
    @staticmethod
    def load_text(filepath: str) -> List[Document]:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()
            
        # Split by double newline to separate paragraphs/chunks
        chunks = [c.strip() for c in raw_text.split('\n\n') if c.strip()]
        
        return [
            Document(id=f"chunk_{i+1}", content=chunk, metadata={"source": filepath})
            for i, chunk in enumerate(chunks)
        ]

    @staticmethod
    def load_raw_text(raw_text: str) -> List[Document]:
        """Loads chunks directly from a string (for UI integration)."""
        chunks = [c.strip() for c in raw_text.split('\n\n') if c.strip()]
        return [
            Document(id=f"chunk_{i+1}", content=chunk, metadata={"source": "ui_upload"})
            for i, chunk in enumerate(chunks)
        ]
