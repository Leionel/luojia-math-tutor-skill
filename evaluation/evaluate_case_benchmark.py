"""
Benchmark evaluation runner for Teaching Case matching in Luojia Math Tutor 2.0.
Evaluates Case Recall@1, Decision Accuracy, and Out-of-Domain New Case Detection.
"""
import json
import sys
from pathlib import Path

# Add apps/api to path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "apps" / "api"))

from app.knowledge.course_service import get_course_service


def run_benchmark():
    benchmark_file = repo_root / "evaluation" / "case_matching_benchmark.json"
    assert benchmark_file.exists(), f"Benchmark file not found at {benchmark_file}"

    with open(benchmark_file, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    service = get_course_service("numerical_analysis")
    matcher = service.case_matcher

    total = len(benchmarks)
    correct_case = 0
    correct_decision = 0
    in_domain_count = 0
    out_domain_count = 0
    out_domain_detected = 0

    print("=" * 65)
    print(f"Luojia Math Tutor 2.0 - Teaching Case Matching Benchmark ({total} items)")
    print("=" * 65)

    for item in benchmarks:
        qid = item["id"]
        q = item["query"]
        expected_id = item["expected_case_id"]
        expected_decisions = item["expected_decision"]
        cat = item["category"]

        res = matcher.match(q, course_id="numerical_analysis")
        matched_id = res.matched_case_id
        decision_val = res.decision.value

        case_ok = (matched_id == expected_id)
        decision_ok = (decision_val in expected_decisions)

        if cat != "out_of_domain":
            in_domain_count += 1
            if case_ok:
                correct_case += 1
        else:
            out_domain_count += 1
            if decision_ok and matched_id is None:
                out_domain_detected += 1

        if decision_ok:
            correct_decision += 1

        status_sym = "[OK]" if (case_ok and decision_ok) else "[WARN]"
        print(f"{status_sym} {qid} | {q[:24]:<26} -> {matched_id or 'None':<28} | {decision_val} (conf={res.confidence:.2f})")

    recall_at_1 = correct_case / in_domain_count if in_domain_count else 0
    decision_acc = correct_decision / total
    ood_detection = out_domain_detected / out_domain_count if out_domain_count else 0

    print("=" * 65)
    print("Benchmark Results Summary:")
    print(f"  Total Queries Tested: {total}")
    print(f"  In-Domain Case Recall@1: {recall_at_1 * 100:.1f}% ({correct_case}/{in_domain_count})")
    print(f"  Overall Decision Accuracy: {decision_acc * 100:.1f}% ({correct_decision}/{total})")
    print(f"  Out-of-Domain NEW_CASE Recall: {ood_detection * 100:.1f}% ({out_domain_detected}/{out_domain_count})")
    print("=" * 65)

    assert recall_at_1 >= 0.90, "Case Recall@1 fell below 90%"
    assert ood_detection == 1.0, "Out-of-domain queries must be detected as NEW_CASE"


if __name__ == "__main__":
    run_benchmark()
