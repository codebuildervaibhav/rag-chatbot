"""
Insight Extractor — Native NLP Architecture

Design rationale:
    Replaced cloud-based LLM classification (GPT-4o-mini) with a fully local, 
    deterministic Natural Language Processing (NLP) pipeline.
    
    Why this architecture?
      - Zero API Latency: Executes in <5ms locally.
      - Zero Cost: Completely eliminates token-based billing.
      - Offline Capable: Can run entirely within an air-gapped or local environment.
      - 100% Deterministic: Will never hallucinate invalid JSON or stray from allowed enum values.

Extraction strategy:
    Intent: Uses a hybrid of NLTK Part-of-Speech (POS) tagging (to detect questions 
            and imperative commands) and targeted heuristics (for complaints/greetings).
    Sentiment: Uses VADER (Valence Aware Dictionary and sEntiment Reasoner), which is 
               highly optimized for social media and chat contexts, natively handling 
               negation, capitalization, and punctuation intensity.
"""

import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize VADER analyzer once (it loads a lexicon into memory)
vader_analyzer = SentimentIntensityAnalyzer()

# ── Heuristic Vocabulary for Non-Structural Intents ──────────────────────────────

COMPLAINT_WORDS: frozenset[str] = frozenset({
    "broken", "error", "bug", "issue", "fail", "failed", "failure",
    "wrong", "bad", "terrible", "awful", "problem", "crash", "crashed",
    "not working", "doesn't work", "can't", "cannot", "unable",
    "frustrated", "disappointed", "annoying", "useless", "slow", "stuck",
    "exception", "traceback"
})

GREETING_WORDS: frozenset[str] = frozenset({
    "hello", "hi", "hey", "good morning", "good evening", "good afternoon",
    "howdy", "greetings", "sup", "what's up", "yo", "hiya"
})


def extract_intent_via_pos(text: str, tokens: list[str], tags: list[tuple[str, str]]) -> str:
    """
    Determines intent using sentence structure and POS tags.
    """
    lower_text = text.lower()

    # 1. Greeting Check (Fast lookup)
    if len(tokens) <= 3 and any(word in lower_text for word in GREETING_WORDS):
        return "greeting"

    # 2. Query Detection (Structural)
    # WDT (Wh-determiner: which, what), WP (Wh-pronoun: who, what), WRB (Wh-adverb: how, where, why)
    is_question = "?" in text or any(tag[1] in ['WDT', 'WP', 'WRB'] for tag in tags)
    if is_question:
        return "query"

    # 3. Request/Command Detection (Structural)
    # If the sentence starts with a Base Verb (VB) or includes imperative politeness.
    # e.g., "Build me an API" -> 'Build' is tagged as VB.
    if "please" in lower_text or "can you" in lower_text or "could you" in lower_text:
        return "request"
        
    if tags:
        first_word_tag = tags[0][1]
        if first_word_tag == 'VB':
            return "request"

    # 4. Complaint Detection (Heuristic Fallback)
    # POS tagging struggles with complaints ("This code is bad" is just Noun-Verb-Adjective).
    if any(word in lower_text for word in COMPLAINT_WORDS):
        return "complaint"

    return "general"


def extract_sentiment_via_vader(text: str) -> str:
    """
    Determines sentiment using VADER polarity scores.
    Returns compound score mapped to positive, negative, or neutral.
    """
    scores = vader_analyzer.polarity_scores(text)
    compound = scores['compound']
    
    # VADER threshold standards:
    # >= 0.05 is Positive, <= -0.05 is Negative, strictly between is Neutral.
    if compound >= 0.05:
        return "positive"
    elif compound <= -0.05:
        return "negative"
    else:
        return "neutral"


async def extract_insights_native(message: str) -> dict:
    """
    Extract intent and sentiment using the native local architecture.
    
    Args:
        message: The user message to classify.

    Returns:
        Dict with "intent" and "sentiment" — guaranteed to return a result instantly.
    """
    try:
        # Tokenize and tag part-of-speech once per message
        tokens = nltk.word_tokenize(message)
        tags = nltk.pos_tag(tokens)
        
        intent = extract_intent_via_pos(message, tokens, tags)
        sentiment = extract_sentiment_via_vader(message)
        
        return {"intent": intent, "sentiment": sentiment}
        
    except Exception as e:
        # Absolute failsafe if NLTK data is missing or parsing fails
        print(f"NLP Extraction Error: {e}")
        return {"intent": "general", "sentiment": "neutral"}