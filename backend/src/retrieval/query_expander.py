from abc import ABC, abstractmethod
from openai import OpenAI
import os

class QueryExpander(ABC):
    @abstractmethod
    def expand(self, query: str) -> str:
        pass

class MockVertexExpander(QueryExpander):
    """
    STRICT COMPLIANCE: Mocks the vertexai.generative_models.GenerativeModel.
    Used for the static CLI benchmark in main.py.
    """
    EXPANSIONS = {
        "How does the system handle peak load?": 
            "How does the architecture manage burst traffic, autoscaling, concurrency, and high demand through dynamic worker pools and Kafka?",
        "What is the procedure for the blue screen?": 
            "What is the fault tolerance, resiliency, circuit breaker, and fallback mechanism for node failures and timeouts?",
        "How do we stop the spinning wheel of death?": 
            "How does the system optimize latency, reduce compute expenditure, and implement semantic caching?"
    }

    def expand(self, query: str) -> str:
        return self.EXPANSIONS.get(query, f"{query} - technical system design context")

class OpenAIExpander(QueryExpander):
    """
    DYNAMIC UI MODE: Uses GPT-4o-mini to expand queries for any custom text uploaded in the UI.
    """
    def __init__(self):
        # Allow missing key gracefully so the app can start without it (will fail on execution if not set)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy-key-for-init"))

    def expand(self, query: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system", 
                    "content": "You are a Retrieval Engineer. Rewrite the user's query into a technical paragraph optimized for vector search. Focus on synonyms and architectural keywords. Do not answer the question."
                }, {"role": "user", "content": query}]
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback if OpenAI fails (e.g. no key)
            return f"{query} - (OpenAI Expansion Failed: {str(e)})"
