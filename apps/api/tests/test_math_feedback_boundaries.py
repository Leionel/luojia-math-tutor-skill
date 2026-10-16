"""Exact counterexamples and fixed-response delivery contracts, not model scores."""
from dataclasses import replace
from fractions import Fraction
import json

import pytest

from app.config import Settings
from app.math_tools.step_checker import check_step
from app.math_tools.step_runtime import verify_student_step
from app.math_tools.verifier import bound_step_verdict, parse_math
from app.tutor.answer_guard import AnswerDeliveryError, check_delivery
from app.tutor.graph import TutorWorkflow
from app.tutor.teaching_decision import resolve_decision
from test_agent_graph import make_config, make_repository, make_state


@pytest.mark.parametrize("left,right", [
    ("1.0000000000000001", "1"),
    ("0.10000000000000001", "0.1"),
    ("0.99999999999999999", "1"),
    ("999999999999.99999", "1000000000000"),
])
def test_exact_decimal_counterexamples(left, right):
    # Independent stdlib arithmetic establishes the counterexample.
    assert Fraction(left) != Fraction(right)
    result, mistake = check_step(f"{left}={right}")
    assert result.is_correct is False and result.eligible_learning_evidence
    assert mistake is None


@pytest.mark.parametrize("message,correct", [
    ("0.1+0.2=0.3", True),
    ("1.0000000000000001=1.0000000000000001", True),
    ("d(1.0000000000000001*x)/dx=1", False),
    ("d(1.0000000000000001*x)/dx=1.0000000000000001", True),
    ("|0.10000000000000001 0; 0 1|=0.1", False),
    ("|0.10000000000000001 0; 0 1|=0.10000000000000001", True),
])
def test_exact_decimal_derivative_and_determinant(message, correct):
    result, _ = check_step(message)
    assert result.is_correct is correct and result.eligible_learning_evidence


@pytest.mark.parametrize("literal", ["1e-400", "1e-1000000", "1e1000000", "0."+"1"*65])
def test_decimal_budgets_reject_before_exact_integer_allocation(literal):
    with pytest.raises(ValueError):
        parse_math(literal)
    result, _ = check_step(f"{literal}=0")
    assert result.is_correct is None and not result.eligible_learning_evidence


@pytest.mark.parametrize("candidate,sign_error", [("1.1", False), ("1.10000000000000001", True), ("sqrt(2)", False)])
def test_determinant_diagnosis_requires_exact_wrong_sum(candidate, sign_error):
    if candidate != "sqrt(2)":
        assert (Fraction(candidate) == Fraction("0.10000000000000001") + 1) is sign_error
    result, mistake = check_step(f"|0.10000000000000001 1;1 1|={candidate}")
    assert result.is_correct is False
    assert result.eligible_learning_evidence
    assert (mistake is not None) is sign_error


@pytest.mark.asyncio
async def test_real_worker_retains_decimal_evidence():
    result, _ = await verify_student_step("|0.10000000000000001 0; 0 1|=0.1")
    assert result.is_correct is False and result.eligible_learning_evidence
    assert result.version == "step-v2"


def decision_raw(correct=False):
    decision = dict(claim_ref="claim:current", evidence_refs=["verifier:deterministic"],
        known_conditions=[], missing_conditions=[], claim_status="supported" if correct else "contradicted",
        action="confirm_local" if correct else "correct_claim", disclosure="scaffolded", reason="本步判定", assessments=[])
    return "[TEACHING_DECISION]"+json.dumps(decision)+"[/TEACHING_DECISION][OUTPUT]"+("这一步正确。" if correct else "这一步不对。")


@pytest.mark.parametrize("message,correct", [("d(x^2)/dx=2*x", True), ("d(x^2)/dx=x", False)])
def test_decision_cannot_reverse_a_bound_local_receipt(message, correct):
    result, _ = check_step(message)
    state = {**make_state(message), "verifier_result": result}
    decision, ui = resolve_decision(decision_raw(not correct), state)
    assert decision["status"] == "fallback" and ui is None
    assert decision["reason_code"] == "deterministic_verdict_conflict"
    assert resolve_decision(decision_raw(correct), state)[0]["status"] == "accepted"


@pytest.mark.parametrize("change", ["old_version", "wrong_input", "scoped", "reference"])
def test_local_feedback_gate_does_not_generalize_receipts(change):
    message = "d(x^2)/dx=2*x"
    result, _ = check_step(message)
    if change == "old_version": result = replace(result, version="step-v1")
    if change == "wrong_input": result = replace(result, input_hash="0"*64)
    if change == "scoped": result = replace(result, scope_complete=False)
    if change == "reference": result = replace(result, origin="system_calculation")
    assert bound_step_verdict(message, result) is None


@pytest.mark.parametrize("text,verdict,conflict", [
    ("这一步不对。", True, True),
    ("你的求导结果错误。", True, True),
    ("这一步正确。", False, True),
    ("不能说这一步不对。", True, False),
    ("如果这一步不对，需要找差异。", True, False),
    ("学生说：“这一步不对。”", True, False),
    ("这一步正确；这不证明整个题目。", True, False),
    ("这一步正确性尚未确定。", False, False),
    ("这一步正确与否，需要核对。", False, False),
    ("这一步正确吗？", False, False),
])
def test_explicit_delivery_verdict_conflicts(text, verdict, conflict):
    assert ("deterministic_verdict_contradiction" in check_delivery(
        text, student_step_verdict=verdict).violations) is conflict


@pytest.mark.asyncio
@pytest.mark.parametrize("repair_correct", [True, False])
async def test_teacher_repairs_conflict_before_delivery_or_withholds(repair_correct):
    message = "d(x^2)/dx=2*x"
    result, _ = check_step(message)
    workflow = TutorWorkflow(Settings(teaching_decision_enabled=True), make_repository())
    responses = iter([decision_raw(False), "这一步正确，导数为2*x；仅核对当前求导。" if repair_correct else "这一步不对。"])
    calls = []
    async def stream(*args, **kwargs):
        calls.append(1)
        yield {"type": "content", "content": next(responses)}
    workflow.llm.stream = stream
    state = {**make_state(message), "verifier_result": result}
    config = make_config()
    if repair_correct:
        response = await workflow.teacher_node(state, config)
        assert response["answer_guard"]["status"] == "repaired"
        assert response["teaching_decision"]["status"] == "fallback"
        assert response["intelligent_ui"] is None
        assert "这一步不对" not in response["final_output"]
        assert config["configurable"]["on_token"].await_count == 1
    else:
        with pytest.raises(AnswerDeliveryError):
            await workflow.teacher_node(state, config)
        config["configurable"]["on_token"].assert_not_awaited()
    assert len(calls) == 2
