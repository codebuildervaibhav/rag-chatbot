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

from database import get_messages_for_conversation
from typing import Optional

@router.get("/benchmark")
async def run_benchmark(conversation_id: Optional[str] = None):
    """Runs the benchmark on the 3 required queries and returns a markdown report."""
    
    # Load the benchmark dataset if not already loaded in the global store
    if rag_engine.store.index.ntotal == 0:
        doc_path = os.path.join(os.path.dirname(__file__), "..", "src", "data", "architecture_doc.txt")
        docs = DatasetLoader.load_text(doc_path)
        rag_engine.load_documents("\n\n".join([d.content for d in docs]))

    # If conversation_id is provided, do the dynamic Answer-to-Chunk mapping benchmark
    if conversation_id:
        messages = get_messages_for_conversation(conversation_id)
        if not messages:
            return {"report": "### 📊 Dynamic Benchmark Failed\n\nNo messages found in this conversation to analyze."}
            
        # Group pairs of User Question -> Assistant Answer
        pairs = []
        for i in range(len(messages) - 1):
            if messages[i]["role"] == "user" and messages[i+1]["role"] == "assistant":
                pairs.append((messages[i]["content"], messages[i+1]["content"]))
        
        # Take the last 3 pairs
        pairs = pairs[-3:]
        
        if not pairs:
            return {"report": "### 📊 Dynamic Benchmark Failed\n\nNo User-Assistant message pairs found."}

        report = f"### 📊 Dynamic Conversation Benchmark (Conversaton ID: `{conversation_id[:8]}...`)\n\n"
        report += "*(Generated dynamically by mapping AI answers to the closest chunk as Ground Truth)*\n\n"
        
        for q, a in pairs:
            # 1. Reverse search for ground truth
            a_vec = rag_engine.embedder.embed_text(a)
            a_res = rag_engine.store.search(a_vec, top_k=1)
            if not a_res:
                continue
            
            ground_truth_id = a_res[0][0]
            
            # 2. Run Strategy A
            res_a = rag_engine.orchestrator.run_strategy_a(q)
            
            # 3. Run Strategy B (using the live OpenAIExpander)
            res_b = rag_engine.orchestrator.run_strategy_b(q)
            
            report += f"**User Query**: `{q}`\n"
            report += f"**Ground Truth Identified**: `{ground_truth_id}` *(Reverse-mapped from AI response)*\n"
            report += f"**Expanded Query (Strategy B)**: `{res_b['expanded_query']}`\n\n"
            report += "| Rank | Strategy A (Raw) | Strategy B (Expanded) |\n"
            report += "| :--- | :--- | :--- |\n"
            
            for i in range(3):
                chunk_a = f"{res_a['results'][i][0]} ({res_a['results'][i][1]:.2f})" if i < len(res_a['results']) else "N/A"
                if chunk_a.startswith(ground_truth_id): chunk_a = f"**{chunk_a}** ✅"
                
                chunk_b = f"{res_b['results'][i][0]} ({res_b['results'][i][1]:.2f})" if i < len(res_b['results']) else "N/A"
                if chunk_b.startswith(ground_truth_id): chunk_b = f"**{chunk_b}** ✅"
                
                report += f"| Rank {i+1} | {chunk_a} | {chunk_b} |\n"
            
            report += "\n---\n\n"
            
        return {"report": report}

    # Else: Fall back to static mock benchmark
    benchmark_expander = MockVertexExpander()
    queries = [
        ("How does the system handle peak load?", "chunk_1"),
        ("What is the procedure for the blue screen?", "chunk_2"),
        ("How do we stop the spinning wheel of death?", "chunk_4")
    ]

    report = "### 📊 Strategy A vs 🧠 Strategy B Benchmark Report\n\n"
    report += "*(Generated using the strict assessment constraints and MockVertexExpander)*\n\n"
    
    for query, truth in queries:
        res_a = rag_engine.orchestrator.run_strategy_a(query)
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
