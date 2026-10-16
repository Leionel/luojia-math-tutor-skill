"""Offline evaluator for frozen Teaching Case matching benchmarks."""
import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))


def _load_matcher():
    # Do not use CourseService: it may open a configured persistent store.
    from app.knowledge.case_matcher import TeachingCaseMatcher
    from app.knowledge.graph_repository import CourseGraphRepository

    pack_path = ROOT / "data" / "course_packs" / "numerical_analysis_root_finding.json"
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    repo = CourseGraphRepository(course_id="numerical_analysis")
    repo.load_from_course_pack(pack)
    # Same matcher, graph metadata and policy as CourseService; only the store
    # is omitted so offline evaluation cannot touch approved production data.
    return TeachingCaseMatcher(repo.case_repo, graph_repo=repo), pack_path


def _accepted(item, key, actual):
    expected = item.get(key)
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


def score_items(items, matcher):
    """Score all examples; matcher errors remain failed examples in denominators."""
    totals = defaultdict(lambda: {"n": 0, "case_correct": 0, "decision_compatible": 0, "singleton_decision_correct": 0, "singleton_decision_n": 0, "errors": 0})
    failures = []
    for item in items:
        group = item.get("split", item.get("category", "unspecified"))
        bucket = totals[group]
        bucket["n"] += 1
        expected_decision = item.get("expected_decision")
        singleton = expected_decision if not isinstance(expected_decision, list) else (expected_decision[0] if len(expected_decision) == 1 else None)
        if singleton is not None:
            bucket["singleton_decision_n"] += 1
        try:
            result = matcher.match(item["query"], course_id="numerical_analysis", context=item.get("context") or {})
            cid = result.matched_case_id
            decision = result.decision.value
            case_ok = _accepted(item, "expected_case_id", cid)
            expected_ids = item.get("expected_case_id")
            expected_ids = expected_ids if isinstance(expected_ids, list) else [expected_ids]
            recalled_ids = [c["case_id"] for c in getattr(result, "candidate_cases", [])[:3]]
            case_at_3 = bool(set(recalled_ids) & {c for c in expected_ids if c is not None})
            decision_ok = _accepted(item, "expected_decision", decision)
            bucket["case_correct"] += int(case_ok)
            bucket["decision_compatible"] += int(decision_ok)
            if singleton is not None:
                bucket["singleton_decision_correct"] += int(decision == singleton)
            if not case_ok or not decision_ok:
                failures.append({"id": item.get("id"), "split": group, "query": item["query"], "expected_case_id": item.get("expected_case_id"), "actual_case_id": cid, "expected_decision": item.get("expected_decision"), "actual_decision": decision, "case_ok": case_ok, "case_at_3": case_at_3, "candidate_cases": getattr(result, "candidate_cases", []), "unit_candidates": getattr(result, "unit_candidates", []), "reason": getattr(result, "reason", ""), "decision_compatible": decision_ok, "singleton_decision_ok": singleton is None or decision == singleton})
        except Exception as exc:  # Preserve failure in denominator.
            bucket["errors"] += 1
            failures.append({"id": item.get("id"), "split": group, "query": item.get("query"), "error": f"{type(exc).__name__}: {exc}"})
    return {k: {**v, "case_recall_at_1": v["case_correct"] / v["n"] if v["n"] else None, "acceptable_set_compatibility": v["decision_compatible"] / v["n"] if v["n"] else None, "singleton_decision_accuracy": v["singleton_decision_correct"] / v["singleton_decision_n"] if v["singleton_decision_n"] else None} for k, v in sorted(totals.items())}, failures


def run_benchmark(benchmark_file=None, output_file=None, strict=False):
    benchmark_file = Path(benchmark_file) if benchmark_file else ROOT / "evaluation" / "case_matching_benchmark.json"
    raw = benchmark_file.read_bytes()
    items = json.loads(raw.decode("utf-8"))
    if not isinstance(items, list) or not items:
        raise ValueError("benchmark must be a non-empty JSON array")
    if any(not isinstance(x, dict) for x in items):
        raise ValueError("every benchmark item must be a JSON object")
    ids = [x.get("id") for x in items]
    queries = [x.get("query") for x in items]
    if any(not isinstance(x, str) or not x for x in ids + queries) or len(ids) != len(set(ids)):
        raise ValueError("every item needs a unique non-empty id and query")
    if len(queries) != len(set(queries)):
        raise ValueError("benchmark contains duplicate query strings")
    matcher, pack_path = _load_matcher()
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    known_case_ids = {case["case_id"] for case in pack.get("teaching_cases", [])}
    valid_decisions = {"SAME_CASE", "VARIANT_OF_CASE", "RELATED_CASE", "NEW_CASE", "UNCERTAIN"}
    for index, item in enumerate(items):
        if "expected_case_id" not in item or "expected_decision" not in item:
            raise ValueError(f"benchmark item {item.get('id', index)} is missing expected_case_id or expected_decision")
        case_gold = item["expected_case_id"]
        decision_gold = item["expected_decision"]
        for field, value in (("expected_case_id", case_gold), ("expected_decision", decision_gold)):
            if isinstance(value, list) and not value:
                raise ValueError(f"benchmark item {item.get('id', index)} has empty {field}")
        case_values = case_gold if isinstance(case_gold, list) else [case_gold]
        unknown = [x for x in case_values if x is not None and x not in known_case_ids]
        if unknown:
            raise ValueError(f"benchmark item {item.get('id', index)} has unknown Case ID(s): {unknown}")
        decision_values = decision_gold if isinstance(decision_gold, list) else [decision_gold]
        invalid = [x for x in decision_values if x not in valid_decisions]
        if invalid:
            raise ValueError(f"benchmark item {item.get('id', index)} has invalid decision label(s): {invalid}")
    strata, failures = score_items(items, matcher)
    total = len(items)
    total_decision_compatible = sum(x["decision_compatible"] for x in strata.values())
    error_ids = {f["id"] for f in failures if "error" in f}
    singleton_items = [x for x in items if not isinstance(x.get("expected_decision"), list) or len(x["expected_decision"]) == 1]
    singleton_correct = sum(1 for x in singleton_items if x["id"] not in {f.get("id") for f in failures if f.get("singleton_decision_ok") is False} and x["id"] not in error_ids)
    # In-domain is explicit; old protocol categories and v2 splits both supported.
    in_domain = [x for x in items if x.get("split", x.get("category")) not in ("out_of_domain", "ood", "new_case", "unroutable")]
    ood = [x for x in items if x.get("split", x.get("category")) in ("out_of_domain", "ood")]
    new_case = [x for x in items if x.get("split") == "new_case"]
    case_ok_ids = {f["id"] for f in failures if f.get("case_ok") is False}
    out = {
        "benchmark": str(benchmark_file), "benchmark_sha256": hashlib.sha256(raw).hexdigest(),
        "benchmark_version": "v2" if "v2" in benchmark_file.name else "legacy-compatible",
        "course_pack_sha256": hashlib.sha256(pack_path.read_bytes()).hexdigest(),
        "matcher_source_sha256": hashlib.sha256((ROOT / "apps" / "api" / "app" / "knowledge" / "case_matcher.py").read_bytes()).hexdigest(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "configuration": {"offline": True, "dotenv_loaded": False, "persistent_store_used": False, "course_id": "numerical_analysis", "strict": strict},
        "total": total, "denominators": {"all": total, "in_domain_routable": len(in_domain), "unroutable": sum(1 for x in items if x.get("split") == "unroutable"), "ood": len(ood), "new_case": len(new_case)},
        "case_recall_at_1": {"correct": 0, "total": len(in_domain)},
        "acceptable_set_compatibility": {"correct": total_decision_compatible, "total": total},
        "singleton_decision_accuracy": {"correct": singleton_correct, "total": len(singleton_items), "excluded_multi_gold": total-len(singleton_items)},
        "ood_detection": {"correct": _detection_correct(ood, failures), "total": len(ood)},
        "new_case_detection": {"correct": _detection_correct(new_case, failures), "total": len(new_case)},
        "strata": strata, "failures": failures,
        "limitations": ["This is a deterministic matcher benchmark, not teacher validation or evidence of mathematical correctness.", "Singleton decision accuracy uses only examples with one gold decision; acceptable-set compatibility is a more permissive metric and is not strict decision accuracy.", "Case recall excludes unroutable samples; new_case means an in-course request absent from the frozen Case ontology, while out_of_domain is outside this course scope.", "Unsupported multi-turn history is not simulated; current CaseMatchResult does not expose calibrated uncertainty."],
    }
    # Correctly compute case accuracy for accepted-set labels, including legacy null OOD semantics.
    out["case_recall_at_1"]["correct"] = sum(1 for x in in_domain if x["id"] not in case_ok_ids and x["id"] not in error_ids)
    failed_by_id = {f["id"]: f for f in failures}
    out["case_recall_at_3"] = {"correct": sum(1 for item in in_domain if item["id"] not in error_ids and
        (item["id"] not in failed_by_id or failed_by_id[item["id"]].get("case_ok") or failed_by_id[item["id"]].get("case_at_3"))), "total": len(in_domain)}
    out["retrieval_source_sha256"] = hashlib.sha256((ROOT / "apps/api/app/knowledge/course_retrieval.py").read_bytes()).hexdigest()
    out["ranking_version"] = "course-bm25-v1"
    by_family = defaultdict(lambda: {"n": 0, "case_correct": 0, "decision_compatible": 0, "singleton_decision_correct": 0, "singleton_decision_n": 0, "errors": 0})
    for item in items:
        fam = item.get("family", item.get("category", "unspecified"))
        row = by_family[fam]
        row["n"] += 1
        expected = item["expected_decision"]
        singleton = expected if not isinstance(expected, list) else (expected[0] if len(expected) == 1 else None)
        if singleton is not None:
            row["singleton_decision_n"] += 1
        failed = next((f for f in failures if f.get("id") == item["id"]), None)
        if failed is None:
            row["case_correct"] += 1
            row["decision_compatible"] += 1
            if singleton is not None:
                row["singleton_decision_correct"] += 1
        else:
            row["case_correct"] += int(failed.get("case_ok", False))
            row["decision_compatible"] += int(failed.get("decision_compatible", False))
            if singleton is not None:
                row["singleton_decision_correct"] += int(failed.get("singleton_decision_ok", False))
            row["errors"] += int("error" in failed)
    out["family_metrics"] = {k: {**v, "case_recall_at_1": v["case_correct"] / v["n"], "acceptable_set_compatibility": v["decision_compatible"] / v["n"], "singleton_decision_accuracy": v["singleton_decision_correct"] / v["singleton_decision_n"] if v["singleton_decision_n"] else None} for k, v in sorted(by_family.items())}
    by_script = defaultdict(lambda: {"n": 0, "case_correct": 0, "decision_compatible": 0, "singleton_decision_correct": 0, "singleton_decision_n": 0, "errors": 0})
    failure_by_id = {f.get("id"): f for f in failures}
    for item in items:
        has_latin = bool(re.search(r"[A-Za-z]", item["query"]))
        has_cjk = bool(re.search(r"[\u4e00-\u9fff]", item["query"]))
        key = "mixed_script" if has_latin and has_cjk else "latin_only" if has_latin else "cjk_only" if has_cjk else "other"
        row = by_script[key]
        row["n"] += 1
        expected = item["expected_decision"]
        singleton = expected if not isinstance(expected, list) else (expected[0] if len(expected) == 1 else None)
        if singleton is not None:
            row["singleton_decision_n"] += 1
        failed = failure_by_id.get(item["id"])
        if failed is None:
            row["case_correct"] += 1
            row["decision_compatible"] += 1
            row["singleton_decision_correct"] += int(singleton is not None)
        else:
            row["case_correct"] += int(failed.get("case_ok", False))
            row["decision_compatible"] += int(failed.get("decision_compatible", False))
            row["singleton_decision_correct"] += int(singleton is not None and failed.get("singleton_decision_ok", False))
            row["errors"] += int("error" in failed)
    out["query_script_strata"] = {k: {**v, "case_recall_at_1": v["case_correct"] / v["n"], "acceptable_set_compatibility": v["decision_compatible"] / v["n"], "singleton_decision_accuracy": v["singleton_decision_correct"] / v["singleton_decision_n"] if v["singleton_decision_n"] else None} for k, v in sorted(by_script.items())}
    out["joint_failure_count"] = len(failures)
    out["case_mismatch_count"] = sum(1 for f in failures if f.get("case_ok") is False)
    out["decision_mismatch_count"] = sum(1 for f in failures if f.get("decision_compatible") is False)
    if output_file:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("benchmark_version", "benchmark_sha256", "course_pack_sha256", "matcher_source_sha256", "total", "denominators", "case_recall_at_1", "case_recall_at_3", "singleton_decision_accuracy", "acceptable_set_compatibility", "ood_detection", "new_case_detection", "strata", "family_metrics", "query_script_strata", "joint_failure_count", "case_mismatch_count", "decision_mismatch_count")}, ensure_ascii=False, indent=2))
    print(f"Failures: {len(failures)}; matcher errors: {len(error_ids)}; sha256={out['benchmark_sha256']}")
    if strict and failures:
        return 1
    return 0


def _detection_correct(examples, failures):
    by_id = {f.get("id"): f for f in failures}
    correct = 0
    for item in examples:
        failure = by_id.get(item["id"])
        if failure is None or (failure.get("case_ok") is True and failure.get("decision_compatible") is True):
            correct += 1
    return correct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict", action="store_true", help="exit nonzero when capability samples fail")
    args = parser.parse_args()
    return run_benchmark(args.benchmark, args.output, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
