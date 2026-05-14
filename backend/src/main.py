import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.data.loader import DatasetLoader
from src.embeddings.mock_vertex import MockVertexEmbeddingModel
from src.storage.faiss_store import FAISSVectorStore
from src.expanders.mock_vertex import MockVertexExpander
from src.retrieval.orchestrator import RetrievalOrchestrator
from src.evaluation.metrics import BenchmarkMetrics
from tabulate import tabulate

def run_benchmark():
    embedder = MockVertexEmbeddingModel()
    store = FAISSVectorStore(dimension=embedder.dimension)
    expander = MockVertexExpander()
    orchestrator = RetrievalOrchestrator(store, embedder, expander)

    doc_path = os.path.join(os.path.dirname(__file__), "data", "architecture_doc.txt")
    docs = DatasetLoader.load_text(doc_path)
    store.add_vectors(embedder.embed_batch([d.content for d in docs]), [{"id": d.id, "content": d.content} for d in docs])

    # NOTE: Ground truth is explicitly defined for the static assessment dataset.
    # In the dynamic UI benchmark mode (see routers/documents.py),
    # ground truth is derived via Answer-to-Chunk similarity search, enabling
    # MRR calculation on arbitrary conversations without pre-labeling.
    queries = [
        ("How does the system handle peak load?", "chunk_1"),
        ("What is the procedure for the blue screen?", "chunk_2"),
        ("How do we stop the spinning wheel of death?", "chunk_4")
    ]

    report_data = []
    
    print("\n" + "="*80)
    print("DETAILED RETRIEVAL BENCHMARK")
    print("="*80)

    for query, truth in queries:
        res_a = orchestrator.run_strategy_a(query)
        res_b = orchestrator.run_strategy_b(query)
        
        mrr_a = BenchmarkMetrics.calculate_mrr([r[0] for r in res_a['results']], truth)
        mrr_b = BenchmarkMetrics.calculate_mrr([r[0] for r in res_b['results']], truth)
        
        # Save for JSON
        report_data.append({
            "query": query,
            "ground_truth": truth,
            "strategy_a": {
                "mrr": mrr_a,
                "top_chunks": [{"id": r[0], "score": r[1], "content": r[2]["content"][:100] + "..."} for r in res_a['results']]
            },
            "strategy_b": {
                "mrr": mrr_b,
                "expanded_query": res_b["expanded_query"],
                "top_chunks": [{"id": r[0], "score": r[1], "content": r[2]["content"][:100] + "..."} for r in res_b['results']]
            }
        })
        
        # Print detailed table for this query
        print(f"\nQuery: {query}")
        print(f"Ground Truth: {truth}")
        print(f"Strategy B Expansion: {res_b['expanded_query']}")
        
        table = []
        for i in range(3):
            chunk_a = f"{res_a['results'][i][0]} ({res_a['results'][i][1]:.2f})" if i < len(res_a['results']) else "N/A"
            chunk_b = f"{res_b['results'][i][0]} ({res_b['results'][i][1]:.2f})" if i < len(res_b['results']) else "N/A"
            table.append([f"Rank {i+1}", chunk_a, chunk_b])
        
        print(tabulate(table, headers=["Rank", "Strategy A (Raw)", "Strategy B (Expanded)"], tablefmt="grid"))
        print(f"MRR Result -> Strategy A: {mrr_a:.2f} | Strategy B: {mrr_b:.2f}")
        print("-" * 80)

    # Save to JSON
    json_path = os.path.join(os.path.dirname(__file__), "..", "comparison_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4)
        
    print(f"\nStructured comparison report saved to: {os.path.abspath(json_path)}")

if __name__ == "__main__":
    run_benchmark()
