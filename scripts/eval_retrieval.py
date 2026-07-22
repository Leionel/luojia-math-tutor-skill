import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def calculate_metrics(test_cases: list[dict], k_values: list[int] = [3, 5]):
    """Calculate Recall@K for the given test cases."""
    # In a real scenario, this would initialize the LocalVectorStore
    # load the knowledge, and run `search_hybrid(query, ...)`
    # For now, we mock the retrieval results to demonstrate the metric calculation pipeline.
    
    metrics = {f"Recall@{k}": 0.0 for k in k_values}
    total_cases = len(test_cases)
    
    if total_cases == 0:
        return metrics

    for case in test_cases:
        query = case.get("query", "")
        expected_ids = set(case.get("expected_knowledge_ids", []))
        
        # MOCK: Replace this with actual retrieval:
        # results = store.search_hybrid(query, query_vector, k=60, top_n=max(k_values))
        # retrieved_ids = [res["doc_id"] for res in results]
        
        # Simulating dummy retrieved IDs
        retrieved_ids = ["measure_countable_additivity", "dummy_1", "dummy_2", "measure_zero_set", "dummy_3"]
        
        for k in k_values:
            top_k_retrieved = set(retrieved_ids[:k])
            # Calculate intersection
            hits = len(expected_ids.intersection(top_k_retrieved))
            # Recall = hits / total expected
            recall = hits / len(expected_ids) if expected_ids else 0.0
            metrics[f"Recall@{k}"] += recall
            
    # Average across all cases
    for k in k_values:
        metrics[f"Recall@{k}"] /= total_cases
        
    return metrics


def run_evaluation():
    root_dir = Path(__file__).parent.parent
    eval_file = root_dir / "evaluation" / "retrieval_eval.json"
    
    if not eval_file.exists():
        logging.error(f"Evaluation dataset not found: {eval_file}")
        return False
        
    with open(eval_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)
        
    logging.info(f"Loaded {len(test_cases)} test cases.")
    
    metrics = calculate_metrics(test_cases)
    
    logging.info("=== Retrieval Evaluation Results ===")
    for metric, value in metrics.items():
        logging.info(f"{metric}: {value:.4f}")
        
    return True


if __name__ == "__main__":
    success = run_evaluation()
    exit(0 if success else 1)
