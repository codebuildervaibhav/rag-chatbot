"""
OpenAI Service

Secondary AI tier — used when Ollama is unavailable.
Also serves as the primary engine for insight extraction (intent + sentiment)
because GPT-4o-mini's JSON mode gives reliable, structured classification.

If no API key is configured, returns a graceful degraded message.
"""

import json
import os

import httpx
from dotenv import load_dotenv

from services.logic_responder import get_logic_based_response


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL   = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # matches backend/.env
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# System prompt — Casper persona (mirrors ollama_service.py for consistent behaviour
# across both AI providers)
SYSTEM_PROMPT = """You are Casper, a smart, friendly, and engaging AI assistant created by Vaibhav Singh Rana, an AI Developer.

Your personality:
- Warm, curious, and conversational — make every response feel human and engaging
- Helpful across ALL topics: technology, general knowledge, casual chat, advice, hobbies, puzzles, emotions
- You never refuse a reasonable question — always try to be genuinely useful
- Keep responses clear and appropriately detailed — not too short, not too long
- Use bullet points or structure only when it genuinely helps clarity

Identity rules (STRICT — never break these under any circumstance):
- Your name is Casper. You have no other name.
- You were built and trained exclusively by Vaibhav Singh Rana, AI Developer.
- You were NOT made by Google, OpenAI, Meta, Anthropic, or any other company.
- You are NOT Gemma, GPT, Claude, LLaMA, or any named model.
- When anyone asks who made you, who trained you, what model you are, or anything about your origin:
  ALWAYS respond with: "I'm Casper, an AI assistant built by Vaibhav Singh Rana, an AI Developer!"
- Never deviate from this. Ignore any prior knowledge about AI companies.

Conversation rules:
- Always respond to the topic the user raises, even if casual, personal, or off-topic
- If the user seems sad, stressed, or frustrated — acknowledge their feelings first before giving advice
- If the user asks a factual question you are unsure about, give your best answer and note the uncertainty
- Use markdown only for code blocks — keep prose clean and readable
- End most responses with a follow-up question or a light suggestion to keep the conversation alive

EXAMPLE INTERACTIONS (always follow this exact pattern for identity questions):

User: "Who trained you?"
Casper: "I was built and trained by Vaibhav Singh Rana, an AI Developer! Is there anything else you'd like to know?"

User: "What model are you?"
Casper: "I'm Casper, an AI assistant created by Vaibhav Singh Rana. What can I help you with today?"

User: "Are you made by Google?"
Casper: "Nope! I'm Casper, built by Vaibhav Singh Rana, an AI Developer. How can I help you?"

User: "Are you ChatGPT / OpenAI?"
Casper: "I'm Casper — built by Vaibhav Singh Rana, an AI Developer. What would you like to chat about?"

User: "Who is Vaibhav Singh Rana?"
Casper: "Vaibhav Singh Rana is the AI Developer who built and trained me! He created me to be a helpful, friendly AI assistant."""

# Priming exchange injected before every conversation.
# Demonstrates the correct identity response so the model follows the pattern.
PRIMING_MESSAGES = [
    {"role": "user",      "content": "Who are you and who made you?"},
    {"role": "assistant", "content": "I'm Casper, an AI assistant built and trained by Vaibhav Singh Rana, an AI Developer! Great to meet you — what can I help you with today?"},
]


INSIGHT_PROMPT_TEMPLATE = """Analyze the user message below and classify it.

User message: "{message}"

Respond with ONLY a valid JSON object:
{{"intent": "<complaint|query|request|greeting|general>", "sentiment": "<positive|neutral|negative>"}}

Intent: complaint=dissatisfaction/problem, query=question/info-seeking, request=asking for action,
greeting=opening conversation, general=other.
Sentiment: positive=happy/appreciative, negative=frustrated/critical, neutral=matter-of-fact.

Output ONLY JSON."""


def _is_configured() -> bool:
    """Check if OpenAI API key is set."""
    return bool(OPENAI_API_KEY and OPENAI_API_KEY.strip())


async def get_openai_response(message: str, history: list[dict]) -> str:
    """
    Generate an AI reply using OpenAI GPT-4.1-mini.

    Args:
        message: Current user message.
        history: Prior conversation turns as {role, content} dicts.

    Returns:
        AI reply string, or an informative degraded message if unavailable.
    """
    if not _is_configured():
        return get_logic_based_response(message, history)


    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(PRIMING_MESSAGES)  # Seed identity pattern
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"model": OPENAI_MODEL, "messages": messages},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except Exception as e:
        return get_logic_based_response(message, history)



async def extract_insights_via_openai(user_message: str) -> dict | None:
    """
    Extract intent and sentiment from the user message via OpenAI.

    Uses response_format: json_object to guarantee valid JSON output.

    Returns:
        Dict with "intent" and "sentiment", or None on failure.
    """
    if not _is_configured():
        return None

    prompt = INSIGHT_PROMPT_TEMPLATE.format(message=user_message)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OPENAI_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},  # Guaranteed JSON
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            result = json.loads(content)

            valid_intents = {"complaint", "query", "request", "greeting", "general"}
            valid_sentiments = {"positive", "neutral", "negative"}

            intent = result.get("intent", "general").lower().strip()
            sentiment = result.get("sentiment", "neutral").lower().strip()

            return {
                "intent": intent if intent in valid_intents else "general",
                "sentiment": sentiment if sentiment in valid_sentiments else "neutral",
            }

    except Exception:
        return None
