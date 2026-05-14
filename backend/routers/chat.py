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
# from database import update_message_insights  # (Alternative strategy import)
from services.insight_extractor import extract_insights
from services.ollama_service import check_ollama_health, get_chat_response
from services.openai_service import get_openai_response

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

    # ── Generate reply ─────────────────────────────────────────────────────────────
    reply: str
    fallback_used = False

    if request.mode == "local":
        # LOCAL: Try Ollama first. If unreachable, silently fall back to OpenAI.
        ollama_ok = await check_ollama_health()
        if ollama_ok:
            try:
                reply = await get_chat_response(request.message, history)
            except Exception:
                ollama_ok = False  # Ollama failed mid-request

        if not ollama_ok:
            # Silent fallback — use Cloud, flag it so frontend can show amber LED
            fallback_used = True
            reply = await get_openai_response(request.message, history)
    else:
        # CLOUD: OpenAI/Casper directly
        reply = await get_openai_response(request.message, history)

    # ── Extract insights (use cloud if fallback triggered) ─────────────────────
    insight_mode = "cloud" if fallback_used else request.mode
    insights = await extract_insights(request.message, mode=insight_mode)

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
