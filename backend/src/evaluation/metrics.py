from typing import List

class BenchmarkMetrics:
    """Calculates Mean Reciprocal Rank (MRR) for strategy comparison."""
    
    @staticmethod
    def calculate_mrr(retrieved_ids: List[str], ground_truth_id: str) -> float:
        """
        Calculates the reciprocal rank of the ground truth chunk.
        MRR = 1/rank if found, else 0.
        """
        for rank, chunk_id in enumerate(retrieved_ids, 1):
            if chunk_id == ground_truth_id:
                return 1.0 / rank
        return 0.0
