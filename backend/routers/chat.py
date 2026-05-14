"""
Chat Router — handles POST /api/chat

Hybrid Architecture (mode-driven):
    ┌──────────────────────────────────────────────────────────────┐
    │  User Message  +  mode: 'local' | 'cloud'                    │
    │       │                                                       │
    │       ├── local ──► Ollama/Murphy  → conversational reply    │
    │       │             NLP Service    → intent + sentiment       │
    │       │                                                       │
    │       └── cloud ──► OpenAI/Casper  → conversational reply    │
    │                     OpenAI JSON    → intent + sentiment       │
    │                           ↓                                   │
    │                     Keyword rules  → final safety net         │
    └──────────────────────────────────────────────────────────────┘

Request:  { message, history, conversation_id?, mode }
Response: { reply, insights, conversation_id, mode }
"""

from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from database import create_conversation, save_message, touch_conversation
from services.insight_extractor import extract_insights
from rag_engine import rag_engine

router = APIRouter()


# ── Request / Response Models ──────────────────────────────────────────────────

class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = []
    conversation_id: Optional[str] = None
    mode: Literal["local", "cloud"] = "local"


class InsightResult(BaseModel):
    intent: str
    sentiment: str


class ChatResponse(BaseModel):
    reply: str
    insights: InsightResult
    conversation_id: str
    mode: str          # Which mode was requested
    fallback_used: bool = False  # True when Local was requested but Ollama was down


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint — mode-driven hybrid architecture.

    LOCAL mode: Ollama (Murphy) for chat + NLP Service for insights
    CLOUD mode: OpenAI (Casper) for chat + OpenAI JSON mode for insights

    Every turn is persisted to SQLite with the mode recorded on the
    assistant message for traceability.
    """
    # Use a moving window of the last 10 messages to limit context size
    history = [{"role": m.role, "content": m.content} for m in request.history[-10:]]

    # ── Resolve or create conversation ─────────────────────────────────────────
    conv_id = request.conversation_id
    if not conv_id:
        title = request.message[:60] + ("…" if len(request.message) > 60 else "")
        conv_id = create_conversation(title)["id"]

    # ── Save user message ──────────────────────────────────────────────────────
    # To use the UPDATE strategy, capture the return dict to get the ID: 
    # user_msg = save_message(conversation_id=conv_id, role="user", content=request.message)
    save_message(conversation_id=conv_id, role="user", content=request.message)

    # ── Generate RAG Results ───────────────────────────────────────────────────
    reply = ""
    fallback_used = False

    if rag_engine.store.index.ntotal == 0:
        reply = "⚠️ **No document indexed.** Please upload a document context first to perform vector search."
    else:
        if request.mode == "local":
            # Strategy A (Raw Search)
            res = rag_engine.orchestrator.run_strategy_a(request.message)
            reply = f"### 📊 Strategy A: Raw Vector Search\n\n"
            reply += f"**Original Query:** `{res['query']}`\n\n"
            for i, result in enumerate(res['results'], 1):
                chunk_id, score, meta = result
                reply += f"**{i}. {chunk_id}** (Score: {score:.4f})\n> {meta['content']}\n\n"
        else:
            # Strategy B (AI-Enhanced)
            res = rag_engine.orchestrator.run_strategy_b(request.message)
            reply = f"### 🧠 Strategy B: AI-Enhanced Retrieval\n\n"
            reply += f"**Original Query:** `{res['query']}`\n"
            reply += f"**Expanded Query:** `{res['expanded_query']}`\n\n"
            for i, result in enumerate(res['results'], 1):
                chunk_id, score, meta = result
                reply += f"**{i}. {chunk_id}** (Score: {score:.4f})\n> {meta['content']}\n\n"

    # ── Extract insights ───────────────────────────────────────────────────────
    insights = await extract_insights(request.message, mode="local")

    # Example of the slower alternative strategy (updating the user row directly):
    # update_message_insights(user_msg["id"], intent=insights["intent"], sentiment=insights["sentiment"])

    # ── Persist assistant reply ────────────────────────────────────────────────
    save_message(
        conversation_id=conv_id,
        role="assistant",
        content=reply,
        intent=insights["intent"],
        sentiment=insights["sentiment"],
    )
    touch_conversation(conv_id)

    return ChatResponse(
        reply=reply,
        insights=InsightResult(**insights),
        conversation_id=conv_id,
        mode=request.mode,
        fallback_used=fallback_used,
    )
