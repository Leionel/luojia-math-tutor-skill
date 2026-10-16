import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("reliability_eval", Path(__file__).resolve().parents[3] / "scripts/eval_agent_reliability.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

MANIFEST = {"cases": [{"id": "sample", "selector": "tests/test_sample.py::test_contract", "expected_instances": 1}]}
CASE = '<testcase classname="tests.test_sample" name="test_contract">{}</testcase>'


@pytest.mark.parametrize("body", ["<failure/>", "<skipped/>", "<error/>"])
def test_failing_or_skipped_contract_cannot_pass(body):
    report = module.summarize(MANIFEST, "<testsuite>" + CASE.format(body) + "</testsuite>")
    assert not report["passed"] and report["passed_instances"] == 0


def test_missing_duplicate_and_unexpected_cases_are_not_green():
    assert not module.summarize(MANIFEST, "<testsuite/>")["passed"]
    with pytest.raises(ValueError):
        module.summarize(MANIFEST, "<testsuite>" + CASE.format("") * 2 + "</testsuite>")
    with pytest.raises(ValueError):
        module.summarize(MANIFEST, '<testsuite><testcase classname="wrong" name="test_contract"/></testsuite>')
    assert module.summarize(MANIFEST, "<testsuite>" + CASE.format("") + "</testsuite>")["passed"]
