"""Tests for R3.4: Policy comparison from failure feedback."""
import pytest
from app.tutor.policy_comparison import (
    PolicyFailureRecord,
    PolicyExecutionMetrics,
    PolicyComparisonReport,
    audit_decision_against_rubric,
    compare_policies,
)


def test_failure_record_diagnostic_chain_format():
    record = PolicyFailureRecord(
        position="turn:1#step_eval",
        criterion_violated="unverified_universal_convergence_accepted",
        effective_alternative="ask_missing_condition",
        affected_stage="decision_action",
    )
    assert record.diagnostic_chain == "turn:1#step_eval → unverified_universal_convergence_accepted → ask_missing_condition → decision_action"


def test_audit_flags_universal_convergence_overextension():
    rubric = {
        "forbidden": ["Accept the universal convergence guarantee."],
        "required": ["Explain or ask about the gap between a computable local step and convergence, without only declaring the student wrong."],
    }
    decision = {
        "action": "confirm_local",
        "claim_status": "supported",
        "missing_conditions": [],
    }
    failures = audit_decision_against_rubric("turn:2#claim", decision, rubric)
    criteria = [f.criterion_violated for f in failures]
    assert "unverified_universal_convergence_accepted" in criteria
    assert "missing_condition_unprobed" in criteria
    assert all(" → " in f.diagnostic_chain for f in failures)


def test_audit_flags_rejecting_correct_local_step():
    rubric = {
        "forbidden": ["Reject the correct first step."],
    }
    decision = {
        "action": "correct_claim",
        "claim_status": "contradicted",
    }
    failures = audit_decision_against_rubric("turn:1#first_step", decision, rubric)
    assert len(failures) == 1
    assert failures[0].criterion_violated == "correct_local_step_rejected"
    assert failures[0].effective_alternative == "confirm_local"


def test_compare_policies_adopts_clean_improvement():
    failure = PolicyFailureRecord(
        position="turn:1#n02",
        criterion_violated="missing_condition_unprobed",
        effective_alternative="ask_missing_condition",
        affected_stage="decision_action",
    )
    baseline = PolicyExecutionMetrics(
        policy_version="v1.0",
        math_conclusion_status="correct",
        fault_attribution_valid=True,
        evaluation_receipt="reviewed-baseline",
        resource_binding=binding(),
        valid_step_misjudged=False,
        disclosure_boundary_maintained=True,
        call_count=1,
        token_usage=850,
        latency_ms=1200.0,
        failures=[failure],
    )
    candidate = PolicyExecutionMetrics(
        policy_version="v1.1-targeted",
        math_conclusion_status="correct",
        fault_attribution_valid=True,
        evaluation_receipt="reviewed-candidate",
        resource_binding=binding(),
        valid_step_misjudged=False,
        disclosure_boundary_maintained=True,
        call_count=1,
        token_usage=920,
        latency_ms=1250.0,
        failures=[],  # Resolved failure
    )

    report = compare_policies("N02", baseline, candidate)
    assert report.verdict == "adopt_candidate"
    assert len(report.failures_resolved) == 1
    assert len(report.failures_introduced) == 0
    assert report.incremental_cost["token_delta"] == 70
    assert report.incremental_cost["latency_ms_delta"] == 50.0

    dict_repr = report.to_dict()
    assert dict_repr["verdict"] == "adopt_candidate"
    assert "missing_condition_unprobed" in dict_repr["failures_resolved"][0]
    assert dict_repr["candidate_metrics"]["evaluation_receipt"] == "reviewed-candidate"


def binding():
    return {key: "fixed" for key in ("model", "tools_hash", "sources_hash", "disclosure", "scenario_hash", "generation_settings_hash")}


def test_unassessed_or_unbound_comparison_cannot_adopt_candidate():
    failure = PolicyFailureRecord("turn:1", "missing_condition_unprobed", "ask_missing_condition", "decision_action")
    baseline = PolicyExecutionMetrics("p0", failures=[failure])
    candidate = PolicyExecutionMetrics("p1")
    assert compare_policies("N02", baseline, candidate).verdict == "retain_baseline"
    baseline.math_conclusion_status = candidate.math_conclusion_status = "correct"
    baseline.fault_attribution_valid = candidate.fault_attribution_valid = True
    baseline.disclosure_boundary_maintained = candidate.disclosure_boundary_maintained = True
    baseline.evaluation_receipt = candidate.evaluation_receipt = "reviewed"
    baseline.resource_binding = binding()
    candidate.resource_binding = {**binding(), "model": "different"}
    assert compare_policies("N02", baseline, candidate).verdict == "retain_baseline"


def test_moving_failure_to_another_turn_is_not_a_clean_improvement():
    baseline = PolicyExecutionMetrics("p0", failures=[PolicyFailureRecord("turn:1", "wrong", "explain", "answer_guard")])
    candidate = PolicyExecutionMetrics("p1", failures=[PolicyFailureRecord("turn:2", "wrong", "explain", "answer_guard")])
    report = compare_policies("N02", baseline, candidate)
    assert report.verdict == "reject_candidate" and report.failures_introduced


def test_compare_policies_rejects_severe_regressions():
    failure = PolicyFailureRecord(
        position="turn:1#n02",
        criterion_violated="missing_condition_unprobed",
        effective_alternative="ask_missing_condition",
        affected_stage="decision_action",
    )
    baseline = PolicyExecutionMetrics(
        policy_version="v1.0",
        valid_step_misjudged=False,
        disclosure_boundary_maintained=True,
        failures=[failure],
    )
    # Candidate fixes missing condition, but misjudges a valid step
    candidate = PolicyExecutionMetrics(
        policy_version="v1.1-flawed",
        valid_step_misjudged=True,  # Severe regression!
        disclosure_boundary_maintained=True,
        failures=[],
    )

    report = compare_policies("N02", baseline, candidate)
    assert report.verdict == "reject_candidate"
    assert "misjudged a valid step" in report.verdict_rationale


def test_compare_policies_retains_baseline_when_no_gain():
    baseline = PolicyExecutionMetrics(
        policy_version="v1.0",
        valid_step_misjudged=False,
        disclosure_boundary_maintained=True,
        failures=[],
    )
    candidate = PolicyExecutionMetrics(
        policy_version="v1.0-variant",
        valid_step_misjudged=False,
        disclosure_boundary_maintained=True,
        failures=[],
    )

    report = compare_policies("N01", baseline, candidate)
    assert report.verdict == "retain_baseline"
