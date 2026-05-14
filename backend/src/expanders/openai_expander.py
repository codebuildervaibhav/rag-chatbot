from openai import OpenAI
import os
from .mock_vertex import QueryExpander

class OpenAIExpander(QueryExpander):
    """
    OPTIONAL BONUS EXTENSION: Dynamic UI Mode
    Uses GPT-4o-mini to expand queries for any custom text uploaded in the UI.
    """
    def __init__(self):
        # Allow missing key gracefully so the app can start without it
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
