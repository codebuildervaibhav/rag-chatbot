"""
Insight Extractor — Hybrid Architecture

Design rationale:
    Insight extraction is deliberately separated from conversational AI and
    routed by the user's selected mode (local vs cloud):

      LOCAL mode  → NLP Service (NLTK POS tagging + VADER sentiment)
                    Zero API calls, zero cost, <5ms locally.

      CLOUD mode  → OpenAI GPT-4o-mini (JSON mode)
                    Reliable structured classification via API.

      Fallback    → Keyword rules (deterministic, zero dependencies)
                    Guarantees a result even if all services are offline.

    This mirrors the conversational AI tier split:
      Local  → Ollama/Murphy  +  NLP Service
      Cloud  → OpenAI/Casper  +  OpenAI JSON mode
"""

from services.nlp_service import extract_insights_native
from services.openai_service import extract_insights_via_openai


# ── Keyword Vocabulary (final fallback) ───────────────────────────────────────

COMPLAINT_WORDS: frozenset[str] = frozenset({
    "broken", "error", "bug", "issue", "fail", "failed", "failure",
    "wrong", "bad", "terrible", "awful", "problem", "crash", "crashed",
    "not working", "doesn't work", "can't", "cannot", "unable",
    "frustrated", "disappointed", "annoying", "useless", "slow", "stuck",
    "exception", "traceback", "not sure why",
})

QUERY_WORDS: frozenset[str] = frozenset({
    "how", "what", "why", "when", "where", "who", "which",
    "explain", "tell me", "can you explain", "what is", "what are",
    "could you clarify", "i want to understand", "help me understand",
    "is it", "are there", "does it", "do you know", "?",
})

REQUEST_WORDS: frozenset[str] = frozenset({
    "please", "can you", "could you", "create", "build", "make",
    "write", "generate", "help me", "show me", "give me", "provide",
    "add", "implement", "design", "fix", "update", "change", "modify",
    "i need", "i want", "i'd like", "i would like",
})

GREETING_WORDS: frozenset[str] = frozenset({
    "hello", "hi", "hey", "good morning", "good evening", "good afternoon",
    "howdy", "greetings", "sup", "what's up", "yo", "hiya",
    "nice to meet", "glad to",
})

POSITIVE_WORDS: frozenset[str] = frozenset({
    "good", "great", "excellent", "amazing", "awesome", "love", "perfect",
    "wonderful", "fantastic", "thank", "thanks", "appreciate", "helpful",
    "brilliant", "nice", "cool", "interesting", "impressive", "happy",
    "glad", "pleased", "excited", "enjoy", "enjoyed", "works", "solved",
})

NEGATIVE_WORDS: frozenset[str] = frozenset({
    "bad", "terrible", "awful", "horrible", "hate", "wrong", "error",
    "broken", "fail", "frustrated", "disappointed", "angry", "annoying",
    "stupid", "useless", "waste", "slow", "crash", "issue", "bug",
    "cannot", "can't", "unable", "unfortunately", "sad", "exhausted",
    "poor", "disappointing", "confusing", "unclear", "tired",
})


def keyword_extract_insights(message: str) -> dict:
    """
    Deterministic keyword-based final fallback classifier.
    No API, no ML — always returns a valid result.
    """
    lower = message.lower()

    if any(word in lower for word in GREETING_WORDS):
        intent = "greeting"
    elif any(word in lower for word in COMPLAINT_WORDS):
        intent = "complaint"
    elif any(word in lower for word in QUERY_WORDS):
        intent = "query"
    elif any(word in lower for word in REQUEST_WORDS):
        intent = "request"
    else:
        intent = "general"

    pos_count = sum(1 for word in POSITIVE_WORDS if word in lower)
    neg_count = sum(1 for word in NEGATIVE_WORDS if word in lower)

    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {"intent": intent, "sentiment": sentiment}


async def extract_insights(message: str, mode: str = "local") -> dict:
    """
    Route insight extraction based on the selected mode.

    LOCAL mode → NLP Service (NLTK + VADER): instant, offline, zero cost
    CLOUD mode → OpenAI JSON mode: reliable API-based classification
    Fallback   → Keyword rules: guaranteed result, zero dependencies

    Args:
        message: The user message to classify.
        mode:    'local' or 'cloud' — set by the frontend toggle.

    Returns:
        Dict with 'intent' and 'sentiment' — always returns a result.
    """
    if mode == "local":
        # LOCAL: NLTK POS tagging + VADER — runs entirely on this machine
        return await extract_insights_native(message)

    # CLOUD: OpenAI JSON mode — structured, reliable classification
    result = await extract_insights_via_openai(message)
    if result:
        return result

    # Final safety net — zero dependencies
    return keyword_extract_insights(message)
