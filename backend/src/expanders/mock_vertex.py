from abc import ABC, abstractmethod

class QueryExpander(ABC):
    @abstractmethod
    def expand(self, query: str) -> str:
        pass

class MockVertexExpander(QueryExpander):
    """
    STRICT COMPLIANCE: Mocks the vertexai.generative_models.GenerativeModel.
    Used for the static CLI benchmark in main.py to guarantee deterministic evaluation.
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
