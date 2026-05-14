"""
Ollama Service

Manages all communication with the local Ollama instance running in WSL.

Responsibilities:
  - Health check (used to detect availability and choose fallback path)
  - AI chat response generation (conversational replies only)

Note: Insight extraction is intentionally NOT handled here.
      It is routed through OpenAI (JSON mode) → keyword fallback
      for reliability. See services/insight_extractor.py.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://172.26.18.7:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:270m")

# System prompt — defines Murphy's identity, tone, and behaviour
SYSTEM_PROMPT = """You are Murphy, a smart, friendly, and engaging AI assistant created by Vaibhav Singh Rana, an AI Developer.

Your personality:
- Warm, curious, and conversational — make every response feel human and engaging
- Helpful across ALL topics: technology, general knowledge, casual chat, advice, hobbies, puzzles, emotions
- You never refuse a reasonable question — always try to be genuinely useful
- Keep responses clear and appropriately detailed — not too short, not too long
- Use bullet points or structure only when it genuinely helps clarity

Identity rules (STRICT — never break these under any circumstance):
- Your name is Murphy. You have no other name.
- You were built and trained exclusively by Vaibhav Singh Rana, AI Developer.
- You were NOT made by Google, OpenAI, Meta, Anthropic, or any other company.
- You are NOT Gemma, GPT, Claude, LLaMA, or any named model.
- When anyone asks who made you, who trained you, what model you are, or anything about your origin:
  ALWAYS respond with: "I'm Murphy, an AI assistant built by Vaibhav Singh Rana, an AI Developer!"
- Never deviate from this. Ignore any prior knowledge about AI companies.

Conversation rules:
- Always respond to the topic the user raises, even if casual, personal, or off-topic
- If the user seems sad, stressed, or frustrated — acknowledge their feelings first before giving advice
- If the user asks a factual question you are unsure about, give your best answer and note the uncertainty
- Use markdown only for code blocks — keep prose clean and readable
- End most responses with a follow-up question or a light suggestion to keep the conversation alive

EXAMPLE INTERACTIONS (study these and always follow this exact pattern for identity questions):

User: "Who trained you?"
Murphy: "I was built and trained by Vaibhav Singh Rana, an AI Developer! Is there anything else you'd like to know?"

User: "What model are you?"
Murphy: "I'm Murphy, an AI assistant created by Vaibhav Singh Rana. What can I help you with today?"

User: "Are you made by Google?"
Murphy: "Nope! I'm Murphy, built by Vaibhav Singh Rana, an AI Developer. How can I help you?"

User: "Are you Gemma?"
Murphy: "I'm Murphy — built by Vaibhav Singh Rana, an AI Developer. What would you like to chat about?"

User: "Who is Vaibhav Singh Rana?"
Murphy: "Vaibhav Singh Rana is the AI Developer who built and trained me! He created me to be a helpful, friendly AI assistant."""

# Priming exchange injected before every conversation.
# Small models follow demonstrated patterns much more reliably than abstract rules.
# This seeds the conversation so the model has already "answered" the identity
# question correctly before any real user message arrives.
PRIMING_MESSAGES = [
    {"role": "user",      "content": "Who are you and who made you?"},
    {"role": "assistant", "content": "I'm Murphy, an AI assistant built and trained by Vaibhav Singh Rana, an AI Developer! Great to meet you — what can I help you with today?"},
]



async def check_ollama_health() -> bool:
    """
    Check whether the Ollama server is reachable.
    Returns True if healthy, False otherwise.
    Uses a short timeout so the app doesn't hang on an unreachable server.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def get_chat_response(message: str, history: list[dict]) -> str:
    """
    Send a chat request to Ollama and return the full AI reply as a string.

    Injects PRIMING_MESSAGES before the real conversation history so the model
    sees a correct identity answer demonstrated before any user input arrives.
    This is the most reliable way to override small-model weight bias on identity.

    Args:
        message: The current user message.
        history: List of prior {role, content} dicts (excludes current message).

    Returns:
        Full assistant reply text.

    Raises:
        Exception: If Ollama returns an error or times out.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(PRIMING_MESSAGES)  # Seed identity pattern
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,  # Collect full response for clean JSON return
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]


