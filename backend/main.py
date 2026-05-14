"""
AI Chatbot Backend — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import chat, conversations, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the SQLite database on startup."""
    init_db()
    yield


app = FastAPI(
    title="AI Chatbot Backend",
    description="Chat, AI responses, conversation insight extraction, and history.",
    version="2.0.0",
    lifespan=lifespan,
)

# Allow requests from the Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(chat.router,          prefix="/api", tags=["chat"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(documents.router,     prefix="/api/documents", tags=["documents"])


@app.get("/api/health", tags=["health"])
async def health_check():
    """
    Health check endpoint used by the frontend on startup and every 60s.

    Returns availability of each AI service so the frontend can:
      - Auto-select the best available mode on startup
      - Drive the LED indicator accurately per service
    """
    import os
    from services.ollama_service import check_ollama_health

    ollama_ok  = await check_ollama_health()
    openai_ok  = bool(os.getenv("OPENAI_API_KEY", "").strip())

    return {
        "status": "ok",
        "ollama": ollama_ok,   # True = Ollama is reachable
        "openai": openai_ok,   # True = OpenAI API key is configured
    }
