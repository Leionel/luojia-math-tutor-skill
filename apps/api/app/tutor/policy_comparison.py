"""Policy version comparison from failure feedback (R3.4).

Structures failure feedback into:
"position → criterion_violated → effective_alternative → affected_stage"

Compares baseline policy (P0) vs candidate policy (P1) under identical models,
tools, sources and disclosure limits.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Literal

Stage = Literal["context_retrieval", "decision_action", "disclosure_level", "ui_selection", "answer_guard"]
Verdict = Literal["adopt_candidate", "reject_candidate", "retain_baseline"]


@dataclass
class PolicyFailureRecord:
    position: str  # Original answer location or turn identifier, e.g. "turn:1#claim_evaluation"
    criterion_violated: str  # Criterion name, e.g. "unverified_convergence_promoted"
    effective_alternative: str  # Valid pedagogical alternative, e.g. "ask_missing_condition"
    affected_stage: Stage  # Stage where the fault surfaced
    note: str = ""

    @property
    def diagnostic_chain(self) -> str:
        """Formatted as '原回答位置 → 违反的判据 → 有效替代 → 影响的决策阶段'."""
        return f"{self.position} → {self.criterion_violated} → {self.effective_alternative} → {self.affected_stage}"


@dataclass
class PolicyExecutionMetrics:
    policy_version: str
    math_conclusion_status: Literal["correct", "incorrect", "unassessed"] = "unassessed"
    valid_step_misjudged: bool = False
    missing_condition_probed: bool = False
    fault_attribution_valid: bool | None = None
    disclosure_boundary_maintained: bool | None = None
    experiment_goal_valid: bool | None = None
    call_count: int = 1
    token_usage: int | None = None
    latency_ms: float | None = None
    cost_estimate: float | None = None
    failures: list[PolicyFailureRecord] = field(default_factory=list)
    # Opaque receipts point to captured runs and a reviewed assessment; this
    # utility does not generate them or establish experimental fairness itself.
    evaluation_receipt: str | None = None
    resource_binding: dict[str, str] = field(default_factory=dict)


@dataclass
class PolicyComparisonReport:
    scenario_id: str
    baseline_version: str
    candidate_version: str
    baseline_metrics: PolicyExecutionMetrics
    candidate_metrics: PolicyExecutionMetrics
    failures_resolved: list[PolicyFailureRecord]
    failures_introduced: list[PolicyFailureRecord]
    incremental_cost: dict[str, Any]
    verdict: Verdict
    verdict_rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "baseline_version": self.baseline_version,
            "candidate_version": self.candidate_version,
            "baseline_metrics": asdict(self.baseline_metrics),
            "candidate_metrics": asdict(self.candidate_metrics),
            "failure_records_resolved": [asdict(f) for f in self.failures_resolved],
            "failure_records_introduced": [asdict(f) for f in self.failures_introduced],
            "failures_resolved": [f.diagnostic_chain for f in self.failures_resolved],
            "failures_introduced": [f.diagnostic_chain for f in self.failures_introduced],
            "incremental_cost": self.incremental_cost,
            "verdict": self.verdict,
            "verdict_rationale": self.verdict_rationale,
        }


def audit_decision_against_rubric(
    position: str,
    decision: dict[str, Any],
    rubric: dict[str, Any],
) -> list[PolicyFailureRecord]:
    """Audit a single teaching decision against a rubric case and return structured failures."""
    failures: list[PolicyFailureRecord] = []
    forbidden = set(rubric.get("forbidden", []))
    required = set(rubric.get("required", []))
    action = decision.get("action")
    claim_status = decision.get("claim_status")

    # 1. Unverified convergence / overgeneralization promoted
    if "Accept the universal convergence guarantee." in forbidden:
        if claim_status == "supported" and not decision.get("missing_conditions"):
            failures.append(PolicyFailureRecord(
                position=position,
                criterion_violated="unverified_universal_convergence_accepted",
                effective_alternative="ask_missing_condition",
                affected_stage="decision_action",
                note="全称收敛断言未经过充分条件证明即被判定支持",
            ))

    # 2. Rejecting valid first step
    if "Reject the correct first step." in forbidden:
        if action == "correct_claim" and claim_status == "contradicted":
            failures.append(PolicyFailureRecord(
                position=position,
                criterion_violated="correct_local_step_rejected",
                effective_alternative="confirm_local",
                affected_stage="decision_action",
                note="学生正确的局部单步被误判为算错",
            ))

    # 3. Missing conditions not probed
    if "Explain or ask about the gap between a computable local step and convergence, without only declaring the student wrong." in required:
        if action not in {"ask_missing_condition", "explain", "offer_experiment"}:
            failures.append(PolicyFailureRecord(
                position=position,
                criterion_violated="missing_condition_unprobed",
                effective_alternative="ask_missing_condition",
                affected_stage="decision_action",
                note="未向学生指明局部可算与收敛之间的前提缺口",
            ))

    # 4. Disclosure boundary violation
    if decision.get("disclosure") == "full" and rubric.get("disclosure_required") == "scaffolded":
        failures.append(PolicyFailureRecord(
            position=position,
            criterion_violated="disclosure_boundary_breached",
            effective_alternative="scaffolded",
            affected_stage="disclosure_level",
            note="未遵循引导披露边界，直接泄露全量解答",
        ))

    return failures


def compare_policies(
    scenario_id: str,
    baseline_metrics: PolicyExecutionMetrics,
    candidate_metrics: PolicyExecutionMetrics,
) -> PolicyComparisonReport:
    """Compare baseline vs candidate policy under identical resources.

    Main branch retention standard (R3.4 Section 7):
    - Candidate must demonstrate a valid action unavailable in baseline, OR resolve
      at least one documented failure.
    - Candidate MUST NOT introduce new severe mathematical errors, misjudgment of
      valid steps, or disclosure boundary violations.
    - Increment costs must be reported honestly.
    """
    def key(f):
        return (f.position, f.criterion_violated, f.affected_stage)
    baseline_violation_keys = {key(f) for f in baseline_metrics.failures}
    candidate_violation_keys = {key(f) for f in candidate_metrics.failures}

    # Resolved failures = in baseline but not in candidate
    resolved = [f for f in baseline_metrics.failures if key(f) not in candidate_violation_keys]

    # Introduced failures = in candidate but not in baseline
    introduced = [f for f in candidate_metrics.failures if key(f) not in baseline_violation_keys]

    # Delta costs
    call_delta = candidate_metrics.call_count - baseline_metrics.call_count
    token_delta = (
        (candidate_metrics.token_usage - baseline_metrics.token_usage)
        if (candidate_metrics.token_usage is not None and baseline_metrics.token_usage is not None)
        else None
    )
    latency_delta = (
        round(candidate_metrics.latency_ms - baseline_metrics.latency_ms, 2)
        if (candidate_metrics.latency_ms is not None and baseline_metrics.latency_ms is not None)
        else None
    )

    incremental_cost = {
        "call_delta": call_delta,
        "token_delta": token_delta,
        "latency_ms_delta": latency_delta,
        "cost_estimate_delta": candidate_metrics.cost_estimate-baseline_metrics.cost_estimate
            if candidate_metrics.cost_estimate is not None and baseline_metrics.cost_estimate is not None else None,
    }

    # Severe regression checks
    severe_regression = False
    reasons = []

    if candidate_metrics.valid_step_misjudged and not baseline_metrics.valid_step_misjudged:
        severe_regression = True
        reasons.append("candidate misjudged a valid step")

    if not candidate_metrics.disclosure_boundary_maintained and baseline_metrics.disclosure_boundary_maintained:
        severe_regression = True
        reasons.append("candidate violated disclosure boundary")

    if candidate_metrics.math_conclusion_status == "incorrect" and baseline_metrics.math_conclusion_status != "incorrect":
        severe_regression = True
        reasons.append("candidate introduced incorrect mathematical conclusion")

    if introduced:
        severe_regression = True
        reasons.append(f"candidate introduced new failure: {', '.join(f.criterion_violated for f in introduced)}")

    if candidate_metrics.fault_attribution_valid is False:
        severe_regression = True
        reasons.append("candidate fault attribution is invalid")
    if candidate_metrics.experiment_goal_valid is False:
        severe_regression = True
        reasons.append("candidate experiment goal is invalid")
    required_bindings = {"model", "tools_hash", "sources_hash", "disclosure", "scenario_hash", "generation_settings_hash"}
    comparable = (all(baseline_metrics.resource_binding.get(k) for k in required_bindings)
                  and baseline_metrics.resource_binding == candidate_metrics.resource_binding)
    assessed = all(m.evaluation_receipt and m.math_conclusion_status != "unassessed"
                   and m.fault_attribution_valid is not None and m.disclosure_boundary_maintained is not None
                   for m in (baseline_metrics, candidate_metrics))
    valid_costs = all(type(m.call_count) is int and m.call_count >= 0 and
                      all(v is None or isinstance(v, (float, int)) and math.isfinite(v) and v >= 0
                          for v in (m.token_usage, m.latency_ms, m.cost_estimate))
                      for m in (baseline_metrics, candidate_metrics))

    if severe_regression:
        verdict: Verdict = "reject_candidate"
        rationale = f"Candidate introduced severe regression(s): {'; '.join(reasons)}."
    elif not comparable or not assessed or not valid_costs:
        verdict = "retain_baseline"
        rationale = "Insufficient comparable, reviewed evidence; missing bindings, assessments or valid cost receipts."
    elif resolved and candidate_metrics.math_conclusion_status == "correct" and candidate_metrics.disclosure_boundary_maintained is True:
        verdict = "adopt_candidate"
        rationale = f"Candidate resolved {len(resolved)} failure(s) without severe regressions: {'; '.join(r.criterion_violated for r in resolved)}."
    else:
        verdict = "retain_baseline"
        rationale = "Candidate provided no documented improvement over baseline under target criteria."

    return PolicyComparisonReport(
        scenario_id=scenario_id,
        baseline_version=baseline_metrics.policy_version,
        candidate_version=candidate_metrics.policy_version,
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        failures_resolved=resolved,
        failures_introduced=introduced,
        incremental_cost=incremental_cost,
        verdict=verdict,
        verdict_rationale=rationale,
    )
