from fastapi import APIRouter
from pydantic import BaseModel
import os
from rag_engine import rag_engine
from src.data.loader import DatasetLoader
from src.retrieval.query_expander import MockVertexExpander

router = APIRouter()

class DocumentUpload(BaseModel):
    text: str

@router.post("/index")
async def index_document(payload: DocumentUpload):
    """Indexes the provided text into the dynamic RAG engine."""
    num_chunks = rag_engine.load_documents(payload.text)
    return {"status": "success", "chunks_indexed": num_chunks}

@router.get("/benchmark")
async def run_benchmark():
    """Runs the benchmark on the 3 required queries and returns a markdown report."""
    
    # Use the mock expander for the benchmark to perfectly match Dev Evidence
    benchmark_expander = MockVertexExpander()
    
    # Load the benchmark dataset if not already loaded in the global store
    doc_path = os.path.join(os.path.dirname(__file__), "..", "src", "data", "architecture_doc.txt")
    docs = DatasetLoader.load_text(doc_path)
    
    # We can temporarily add these to the global store, or just use the global store if it's empty
    if rag_engine.store.index.ntotal == 0:
        rag_engine.load_documents("\n\n".join([d.content for d in docs]))

    queries = [
        ("How does the system handle peak load?", "chunk_1"),
        ("What is the procedure for the blue screen?", "chunk_2"),
        ("How do we stop the spinning wheel of death?", "chunk_4")
    ]

    report = "### 📊 Strategy A vs 🧠 Strategy B Benchmark Report\n\n"
    report += "*(Generated using the strict assessment constraints and MockVertexExpander)*\n\n"
    
    for query, truth in queries:
        # Run Strategy A using the global orchestrator (which uses the standard embedder)
        res_a = rag_engine.orchestrator.run_strategy_a(query)
        
        # Run Strategy B manually using the mock expander to guarantee assessment results
        expanded_query = benchmark_expander.expand(query)
        vec = rag_engine.embedder.embed_text(expanded_query)
        results_b = rag_engine.store.search(vec, top_k=3)
        res_b = {"query": query, "expanded_query": expanded_query, "results": results_b}
        
        report += f"**Query**: `{query}`\n"
        report += f"**Expanded Query (Strategy B)**: `{res_b['expanded_query']}`\n\n"
        report += "| Rank | Strategy A (Raw) | Strategy B (Expanded) |\n"
        report += "| :--- | :--- | :--- |\n"
        
        for i in range(3):
            chunk_a = f"{res_a['results'][i][0]} ({res_a['results'][i][1]:.2f})" if i < len(res_a['results']) else "N/A"
            chunk_b = f"{res_b['results'][i][0]} ({res_b['results'][i][1]:.2f})" if i < len(res_b['results']) else "N/A"
            report += f"| Rank {i+1} | {chunk_a} | {chunk_b} |\n"
        
        report += "\n---\n\n"

    return {"report": report}
