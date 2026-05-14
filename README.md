# Context-Aware Retrieval Engine (RAG Assessment)

A production-ready Retrieval-Augmented Generation (RAG) pipeline built to demonstrate advanced semantic search, query expansion, and structured evaluation benchmarking.

This repository fulfills the requirements for the **Senior Gen AI Assessment: Semantic RAG & Vector Search**, comparing traditional vector retrieval against AI-enhanced query expansion.

---

## 🎯 Architecture & Objectives

The primary objective of this system is to dynamically ingest raw technical data, generate embeddings, and perform high-accuracy semantic searches. 

A critical component of this project is the **Evaluation Pipeline**, which mathematically compares two distinct retrieval strategies:

### 📊 Strategy A: Raw Vector Search
Traditional embedding-based similarity search. The user's raw input query is embedded and searched directly against the document chunks.

### 🧠 Strategy B: AI-Enhanced Retrieval
An advanced RAG approach utilizing a Language Model (LLM) to rewrite and expand the user's query into a highly optimized, keyword-rich semantic string before performing the vector search. This strategy bridges the "vocabulary gap" between human slang/abstraction and technical documentation.

---

## 🏗️ Modular Architecture

This project is built using **Abstract Base Classes (ABC)** to ensure components are swappable and adhere to strict interfaces, a critical requirement for production systems.

```text
backend/src/
├── embeddings/
│   ├── base.py              # ABC: EmbeddingEngine
│   └── mock_vertex.py       # Simulates vertexai TextEmbeddingModel using sentence-transformers
├── storage/
│   ├── base.py              # ABC: VectorStore
│   └── faiss_store.py       # FAISS implementation with IndexFlatIP (Cosine Similarity)
├── expanders/
│   ├── mock_vertex.py       # Deterministic mock of vertexai GenerativeModel (CLI)
│   └── openai_expander.py   # OPTIONAL: Live GPT-4o-mini expansion for Dynamic UI Mode
├── retrieval/
│   └── orchestrator.py      # Toggles between Strategy A and Strategy B
└── main.py                  # CLI Benchmarking engine
```
By relying on `EmbeddingEngine` and `VectorStore` interfaces, migrating from local FAISS to **Vertex AI Matching Engine** requires zero changes to the `RetrievalOrchestrator`.

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **Embeddings** | `sentence-transformers` | Generates semantic vectors (simulating Vertex AI Gecko) |
| **Vector Database** | `FAISS` (Facebook AI Similarity Search) | Local, high-performance cosine similarity search |
| **Query Expansion** | `OpenAI` / Mocked SDK | LLM-based query rewriting |
| **Backend API** | `FastAPI` (Python) | High-throughput async REST API |
| **Frontend UI** | `React` + `TailwindCSS` | Interactive chatbot and document ingestion dashboard |
| **Testing** | `Pytest` | Automated pipeline and component testing |

---

## 🚀 Setup & Installation

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\Activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```

**Environment Variables:**
Create a `.env` file in the `backend/` directory:
```env
# Required for dynamic UI query expansion
OPENAI_API_KEY=your-api-key-here
```

**Start the Backend Server:**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The Web UI will be available at: **http://localhost:5173**

---

## 📈 Running the Benchmark

The assignment requires a structured comparison of Strategy A vs Strategy B using Mean Reciprocal Rank (MRR). This can be executed in two ways:

### 1. CLI Benchmark (Strict Assessment Mode)
Runs the assessment using the deterministic `MockVertexExpander` to guarantee stable evidence.
```bash
cd backend
python src/main.py
```
*This generates a formatted CLI table and saves the results to `backend/comparison_report.json`.*

### 2. UI Benchmark (Dynamic)
1. Open the Web UI.
2. Click **"Run Benchmark"** in the left sidebar.
3. The system will dynamically inject the Markdown benchmark report directly into the chat interface.

---

## 📋 Submission Evidence & Documentation

As required by the assessment guidelines, please refer to the [retrieval_benchmark.md](./backend/retrieval_benchmark.md) file located in the `backend/` directory. 

This document contains:
1. The **Dev Evidence** tables showing the exact output of the "Strategy A vs Strategy B" comparison.
2. **Technical Documentation** explaining the choice of Cosine Similarity vs. Euclidean Distance.
3. **Migration Plan** detailing how to upgrade the local FAISS implementation to GCP's **Vertex AI Vector Search (Matching Engine)** for production scale.

---

## 🧪 Testing

The repository includes a comprehensive `pytest` suite verifying the retrieval pipeline, FAISS insertion, mock SDK behaviors, and orchestrator logic.

```bash
cd backend
pytest tests/
```

---

*Developed by Vaibhav Gen AI Engineer.*
