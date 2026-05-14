from src.embeddings.mock_vertex import MockVertexEmbeddingModel
from src.storage.faiss_store import FAISSVectorStore
from src.expanders.openai_expander import OpenAIExpander
from src.retrieval.orchestrator import RetrievalOrchestrator
from src.data.loader import DatasetLoader

class RAGEngine:
    def __init__(self):
        # Initialize the global components
        self.embedder = MockVertexEmbeddingModel()
        self.store = FAISSVectorStore(dimension=self.embedder.dimension)
        # Using the OpenAI Expander for the dynamic UI
        self.expander = OpenAIExpander()
        self.orchestrator = RetrievalOrchestrator(self.store, self.embedder, self.expander)

    def load_documents(self, text: str):
        """Loads and indexes raw text into the vector store."""
        docs = DatasetLoader.load_raw_text(text)
        if docs:
            embeddings = self.embedder.embed_batch([d.content for d in docs])
            self.store.add_vectors(embeddings, [{"id": d.id, "content": d.content} for d in docs])
        return len(docs)

# Global singleton to be used by FastAPI routers
rag_engine = RAGEngine()
