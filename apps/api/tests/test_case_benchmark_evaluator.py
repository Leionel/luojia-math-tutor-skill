import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


EVALUATOR_PATH = Path(__file__).resolve().parents[3] / "evaluation" / "evaluate_case_benchmark.py"
spec = importlib.util.spec_from_file_location("case_benchmark_evaluator", EVALUATOR_PATH)
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


class StubMatcher:
    def __init__(self, result=None, error=False):
        self.result = result
        self.error = error
        self.contexts = []

    def match(self, query, course_id, context):
        self.contexts.append(context)
        if self.error:
            raise RuntimeError("deliberate evaluator fixture failure")
        return self.result


def test_score_accepts_gold_sets_and_passes_context():
    matcher = StubMatcher(SimpleNamespace(matched_case_id="CASE_A", decision=SimpleNamespace(value="VARIANT_OF_CASE")))
    items = [{"id": "a", "query": "x", "family": "CASE_A", "split": "context_task", "expected_case_id": ["CASE_B", "CASE_A"], "expected_decision": ["SAME_CASE", "VARIANT_OF_CASE"], "context": {"task_mode": "code_task"}}]
    strata, failures = evaluator.score_items(items, matcher)
    assert matcher.contexts == [{"task_mode": "code_task"}]
    assert strata["context_task"]["n"] == 1
    assert strata["context_task"]["case_correct"] == 1
    assert strata["context_task"]["decision_compatible"] == 1
    assert not failures


def test_score_keeps_matcher_errors_in_denominator():
    matcher = StubMatcher(error=True)
    strata, failures = evaluator.score_items([{"id": "bad", "query": "x", "split": "insufficient_information", "expected_case_id": ["CASE_A"], "expected_decision": ["UNCERTAIN"]}], matcher)
    assert strata["insufficient_information"]["n"] == 1
    assert strata["insufficient_information"]["errors"] == 1
    assert strata["insufficient_information"]["acceptable_set_compatibility"] == 0
    assert strata["insufficient_information"]["singleton_decision_accuracy"] == 0
    assert failures[0]["id"] == "bad"
    assert "deliberate" in failures[0]["error"]


def test_accepts_singleton_and_scalar_gold():
    item = {"expected_case_id": "CASE_A", "expected_decision": ["SAME_CASE"]}
    assert evaluator._accepted(item, "expected_case_id", "CASE_A")
    assert evaluator._accepted(item, "expected_decision", "SAME_CASE")
    assert not evaluator._accepted(item, "expected_case_id", "CASE_B")


def test_duplicate_queries_are_rejected_before_matcher_load(tmp_path, monkeypatch):
    path = tmp_path / "bad.json"
    path.write_text('[{"id":"1","query":"same"},{"id":"2","query":"same"}]', encoding="utf-8")
    monkeypatch.setattr(evaluator, "_load_matcher", lambda: pytest.fail("must reject malformed data first"))
    with pytest.raises(ValueError, match="duplicate query"):
        evaluator.run_benchmark(path)


class RoutedStubMatcher:
    def match(self, query, course_id, context):
        if query == "explode":
            raise RuntimeError("fixture error")
        case_id, decision = {
            "scalar-null": (None, "NEW_CASE"),
            "list-null": (None, "UNCERTAIN"),
            "wrong-case": ("CASE_A", "UNCERTAIN"),
        }[query]
        return SimpleNamespace(matched_case_id=case_id, decision=SimpleNamespace(value=decision))


def test_run_benchmark_ood_uses_case_and_decision_acceptance(tmp_path, monkeypatch, capsys):
    benchmark = tmp_path / "fixture_v2.json"
    pack = tmp_path / "pack.json"
    pack.write_text('{"teaching_cases":[{"case_id":"CASE_A"}]}', encoding="utf-8")
    rows = [
        {"id":"1","query":"scalar-null","split":"out_of_domain","expected_case_id":None,"expected_decision":"NEW_CASE","family":"OOD"},
        {"id":"2","query":"list-null","split":"out_of_domain","expected_case_id":[None],"expected_decision":["NEW_CASE","UNCERTAIN"],"family":"OOD"},
        {"id":"3","query":"wrong-case","split":"out_of_domain","expected_case_id":[None],"expected_decision":["UNCERTAIN"],"family":"OOD"},
        {"id":"4","query":"explode","split":"out_of_domain","expected_case_id":[None],"expected_decision":["NEW_CASE"],"family":"OOD"},
    ]
    benchmark.write_text(__import__("json").dumps(rows), encoding="utf-8")
    monkeypatch.setattr(evaluator, "_load_matcher", lambda: (RoutedStubMatcher(), pack))
    assert evaluator.run_benchmark(benchmark) == 0
    report = __import__("json").loads(capsys.readouterr().out.split("\nFailures:")[0])
    assert report["ood_detection"] == {"correct": 2, "total": 4}
    assert report["strata"]["out_of_domain"]["errors"] == 1
    assert report["singleton_decision_accuracy"]["total"] == 3
    assert report["acceptable_set_compatibility"]["total"] == 4
    assert report["matcher_source_sha256"]


@pytest.mark.parametrize("row, message", [
    ({"id":"1","query":"x","expected_decision":["SAME_CASE"]}, "missing expected_case_id"),
    ({"id":"1","query":"x","expected_case_id":[],"expected_decision":["SAME_CASE"]}, "empty expected_case_id"),
    ({"id":"1","query":"x","expected_case_id":["CASE_A"],"expected_decision":[]}, "empty expected_decision"),
    ({"id":"1","query":"x","expected_case_id":["DOES_NOT_EXIST"],"expected_decision":["SAME_CASE"]}, "unknown Case ID"),
])
def test_run_benchmark_rejects_invalid_gold_before_matching(tmp_path, monkeypatch, row, message):
    benchmark = tmp_path / "bad_v2.json"
    pack = tmp_path / "pack.json"
    pack.write_text('{"teaching_cases":[{"case_id":"CASE_A"}]}', encoding="utf-8")
    benchmark.write_text(__import__("json").dumps([row]), encoding="utf-8")
    class NeverMatch:
        def match(self, *args, **kwargs):
            pytest.fail("invalid gold must be rejected before matching")
    monkeypatch.setattr(evaluator, "_load_matcher", lambda: (NeverMatch(), pack))
    with pytest.raises(ValueError, match=message):
        evaluator.run_benchmark(benchmark)
