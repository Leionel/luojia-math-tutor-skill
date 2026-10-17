"""One-call teaching decisions and a bounded, source-bound OpenUI selection.

The decision is a model opinion. References prove where its inputs came from,
not that the opinion is correct. This module never updates mastery or runs tools.
"""
import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, FiniteFloat

from app.math_tools.verifier import VerifyResult, bound_step_verdict
from app.tutor.prompt_policy import resolve_teaching_policy
from app.tutor.hint_policy import HintLevel
from app.math_tools.exploration_tasks import ExplorationTask

CATALOG = json.loads((Path(__file__).resolve().parents[4] / "protocol/intelligent-ui-catalog.json").read_text(encoding="utf-8"))
CATALOG_PROMPT = (Path(__file__).resolve().parents[4] / "protocol/intelligent-ui-prompt.txt")
DECISION_VERSION = "teaching-decision-v1"
Action = Literal["confirm_local", "correct_claim", "ask_missing_condition", "offer_experiment", "explain", "offer_probe"]
Status = Literal["supported", "partially_supported", "contradicted", "unknown"]


class Assessment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    claim: str = Field(min_length=1, max_length=500)
    status: Status
    evidence_refs: list[str] = Field(max_length=8)


class ExperimentProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question_to_test: str = Field(min_length=1, max_length=300)
    changed_parameter: Literal["initial_value"] = "initial_value"
    suggested_value: FiniteFloat = Field(ge=-1e25, le=1e25)
    candidate_values: list[FiniteFloat] = Field(default_factory=list, max_length=2)
    observable: str = Field(min_length=1, max_length=200)


class StructuredExperimentProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_to_test: str = Field(min_length=1, max_length=300)
    changed_parameter: Literal["task_parameters"] = "task_parameters"
    tasks: list[ExplorationTask] = Field(min_length=1, max_length=2)
    observable: str = Field(min_length=1, max_length=200)


class TeachingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    claim_ref: Literal["claim:current"]
    evidence_refs: list[str] = Field(max_length=12)
    known_conditions: list[str] = Field(max_length=8)
    missing_conditions: list[str] = Field(max_length=8)
    claim_status: Status
    action: Action
    disclosure: Literal["full", "scaffolded"]
    reason: str = Field(min_length=1, max_length=360)
    assessments: list[Assessment] = Field(default_factory=list, max_length=6)
    experiment_proposal: ExperimentProposal | StructuredExperimentProposal | None = None



class UISelection(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    component: Literal["SourceExcerpt", "ConditionChecklist", "PredictionForm", "ParameterCompare", "RunTraceChart"]
    evidence_ref: str = Field(min_length=1, max_length=160)


def source_bundle(state: dict, tool_evidence: list | None = None) -> dict:
    """Only bounded server inputs receive selectable source IDs."""
    context = state.get("learning_context") or {}
    sources = [{"id": "claim:current", "kind": "student_claim", "data":
                (context.get("student_claim") or {}).get("text", state.get("message", ""))}]
    for entry in state.get("personal_context", []):
        sources.append({"id": entry["id"], "kind": "personal_judgment", "data": entry})
    for key in ("parameters", "rows", "exact_check", "linear_check", "citation", "condition_review", "finding", "code_excerpt", "condition", "original_claim", "personal_relations", "experiments", "revisions", "teaching_focus"):
        if key in context:
            sources.append({"id": f"context:{key}", "kind": "scoped_check" if key in {"exact_check", "linear_check"} else "reference", "data": context[key]})
    verifier = state.get("verifier_result")
    if isinstance(verifier, VerifyResult) and (verifier.verified or verifier.execution_status == "succeeded"):
        sources.append({"id": "verifier:deterministic", "kind": "scoped_check", "data": asdict(verifier)})
    if state.get("verification_result"):
        sources.append({"id": "review:model", "kind": "model_opinion", "data": state["verification_result"]})
    for hit in state.get("hits", [])[:5]:
        item = hit.item
        sources.append({"id": f"knowledge:{item.id}", "kind": "reference", "data": {"concept": item.concept_zh, "excerpt": item.description[:900]}})
    from app.knowledge.targeted_retrieval import TargetedRetrievalResult, TargetedEvidenceSnippet
    result = state.get("targeted_result")
    targeted = result.snippets if isinstance(result, TargetedRetrievalResult) else state.get("targeted_snippets", [])
    for snippet in (targeted or [])[:3]:
        if (not isinstance(snippet, TargetedEvidenceSnippet) or snippet.review_status != "verified"
                or not re.fullmatch(r"targeted:[0-2]", snippet.id)
                or snippet.scope != "reference_provenance_only"
                or not re.fullmatch(r"[a-f0-9]{64}", snippet.content_hash) or not snippet.graph_revision):
            continue
        sid = snippet.id if hasattr(snippet, "id") else snippet.get("id")
        title = snippet.title if hasattr(snippet, "title") else snippet.get("title", "")
        content = snippet.content if hasattr(snippet, "content") else snippet.get("content", "")
        provenance = snippet.provenance if hasattr(snippet, "provenance") else snippet.get("provenance", "")
        goal = snippet.goal if hasattr(snippet, "goal") else snippet.get("goal", "")
        sources.append({
            "id": sid,
            "kind": "reference",
            "data": {
                "title": title,
                "excerpt": content[:900],
                "provenance": provenance,
                "goal": goal,
                "scope": "reference_provenance_only",
                "review_status": snippet.review_status,
                "content_hash": snippet.content_hash,
                "graph_revision": snippet.graph_revision,
            }
        })
    for index, evidence in enumerate(tool_evidence or []):
        sources.append({"id": f"tool:{index}", "kind": "scoped_check" if evidence.get("execution_succeeded") else "unavailable", "data": evidence})
    # Version of selected source AND claim; never reapply a decision to another turn.
    encoded = json.dumps({"ref": context.get("ref"), "sources": sources}, ensure_ascii=False, sort_keys=True, allow_nan=False)
    return {"source_hash": hashlib.sha256(encoded.encode()).hexdigest(), "context_ref": context.get("ref"), "sources": sources}


def decision_prompt(state: dict) -> dict:
    policy = resolve_teaching_policy(state["intent"], state.get("mode", "socratic"), HintLevel(state.get("hint_level", 0)), state.get("pedagogical_action"))
    bundle = source_bundle(state)
    # Data is already in RUNTIME_CONTEXT. List locators here rather than
    # paying for a second copy of trajectory, source text and verifier output.
    references = {**bundle, "sources": [{"id": source["id"], "kind": source["kind"]} for source in bundle["sources"]]}
    return {"version": DECISION_VERSION, "allowed_actions": ["confirm_local", "correct_claim", "ask_missing_condition", "offer_experiment", "explain", "offer_probe"],
            "disclosure": policy["disclosure"], "sources": references,
            "catalog": {key: CATALOG[key] for key in ("version", "selection_limit", "selection_schema", "rules")},
            "openui_component_signatures": CATALOG_PROMPT.read_text(encoding="utf-8").split("## Component Signatures", 1)[-1].split("## Hoisting", 1)[0][:2400] if CATALOG_PROMPT.is_file() else "",
            "decision_schema": {"claim_ref": "claim:current", "evidence_refs": ["available source id"],
                "known_conditions": ["condition explicitly stated or scoped by evidence"], "missing_conditions": ["needed but unknown condition"],
                "claim_status": "supported|partially_supported|contradicted|unknown", "action": "one allowed action",
                "disclosure": policy["disclosure"], "reason": "short teaching reason, not hidden reasoning",
                "assessments": [{"claim": "a local subclaim", "status": "supported|partially_supported|contradicted|unknown", "evidence_refs": ["available id"]}],
                "experiment_proposal": {"question_to_test": "实验目的", "changed_parameter": "initial_value", "suggested_value": -2.0, "candidate_values": [1.5], "observable": "观察指标"}},
            "instruction": "同一次回答先输出 [TEACHING_DECISION]严格JSON[/TEACHING_DECISION]，可选 [INTELLIGENT_UI]JSON数组[/INTELLIGENT_UI]，最后 [OUTPUT]学生正文。判断只是模型意见，不更改 verified/mastery。局部正确可直接承认，不必强制提问；混合主张分别评价。unknown不是错误，缺函数/方法/初值/比较量时先澄清。action为offer_experiment时必须提供experiment_proposal（且changed_parameter推荐值与当前不同）；非offer_experiment时禁止包含该字段。full要给完整过程，不强迫预测或追问。选择UI仅使用组件名和已有evidence_ref，不造数据，不把学生预测代填。正文即使UI不可用也须独立完整。"}


def _section(raw: str, name: str):
    found = re.findall(rf"\[{name}\]\s*(.*?)\s*\[/{name}\]", raw, re.S)
    if len(found) != 1 or len(found[0]) > 12000:
        raise ValueError("missing_or_invalid_section")
    return json.loads(found[0])


def visible_answer(raw: str) -> str:
    """Remove protocol even when malformed; a partial protocol is never a reply."""
    output = re.search(r"\[OUTPUT\]\s*(.*)$", raw, re.S | re.I)
    if output:
        return output.group(1).strip()
    return re.sub(r"\[(TEACHING_DECISION|INTELLIGENT_UI)\].*?(?:\[/\1\]|$)", "", raw, flags=re.S).strip()


def resolve_decision(raw: str, state: dict, tool_evidence=None) -> tuple[dict, dict | None]:
    bundle = source_bundle(state, tool_evidence)
    fallback = {"version": DECISION_VERSION, "status": "fallback", "origin": "model_opinion", "source_hash": bundle["source_hash"], "reason_code": "invalid_decision", "fallback_action": state.get("pedagogical_action", "explain")}
    try:
        decision = TeachingDecision.model_validate(_section(raw, "TEACHING_DECISION"))
        available = {source["id"]: source for source in bundle["sources"]}
        refs = [*decision.evidence_refs, *(ref for item in decision.assessments for ref in item.evidence_refs)]
        if any(ref not in available or available[ref]["kind"] == "unavailable" for ref in refs):
            raise ValueError("unknown_evidence_ref")
        if any(len(text) > 500 or not text.strip() for text in [*decision.known_conditions, *decision.missing_conditions]):
            raise ValueError("invalid_condition")
        expected = decision_prompt(state)["disclosure"]
        if decision.disclosure != expected or expected == "full" and decision.action != "explain":
            raise ValueError("disclosure_conflict")
        if decision.claim_status == "supported" and decision.missing_conditions:
            raise ValueError("unsupported_conditions")
        if decision.action == "confirm_local" and decision.claim_status not in {"supported", "partially_supported"}:
            raise ValueError("confirmation_conflict")
        if decision.action == "correct_claim" and decision.claim_status not in {"contradicted", "partially_supported"}:
            raise ValueError("correction_conflict")
        if decision.action == "ask_missing_condition" and not decision.missing_conditions:
            raise ValueError("missing_question_basis")
        if decision.claim_status != "unknown" and not any(ref != "claim:current" for ref in refs):
            raise ValueError("no_supporting_evidence")
        if decision.claim_status == "supported" and not any(available[ref]["kind"] in {"scoped_check", "reference"} for ref in refs):
            raise ValueError("no_supporting_evidence")
        verdict = bound_step_verdict(state.get("message", ""), state.get("verifier_result"))
        claim = bundle["sources"][0]["data"]
        if claim == state.get("message") and (
                verdict is True and (decision.claim_status == "contradicted" or decision.action == "correct_claim")
                or verdict is False and decision.claim_status == "supported"):
            raise ValueError("deterministic_verdict_conflict")
        if decision.action == "offer_experiment":
            if not isinstance(decision.experiment_proposal, ExperimentProposal):
                raise ValueError("missing_experiment_proposal")
            context = state.get("learning_context") or {}
            params = context.get("parameters") or {}
            if (context.get("ref") or {}).get("kind") != "root_lab" or params.get("method") != "newton":
                raise ValueError("invalid_experiment_context")
            if any(abs(value) > 1e25 or value == params.get("initial_value") for value in decision.experiment_proposal.candidate_values):
                raise ValueError("invalid_experiment_candidates")
            if decision.experiment_proposal.changed_parameter in params:
                cur_val = params[decision.experiment_proposal.changed_parameter]
                if isinstance(cur_val, (int, float)) and abs(cur_val - decision.experiment_proposal.suggested_value) < 1e-12:
                    raise ValueError("experiment_parameter_unchanged")
        elif decision.experiment_proposal is not None:
            raise ValueError("unrequested_experiment_proposal")
        accepted = {"version": DECISION_VERSION, "status": "accepted", "origin": "model_opinion", **decision.model_dump(), **bundle}
    except (ValueError, TypeError, ValidationError) as error:
        if isinstance(error, ValueError) and str(error) in {"unknown_evidence_ref", "disclosure_conflict", "unsupported_conditions", "confirmation_conflict", "correction_conflict", "missing_question_basis", "no_supporting_evidence", "missing_experiment_proposal", "experiment_parameter_unchanged", "unrequested_experiment_proposal", "invalid_experiment_context", "invalid_experiment_candidates", "deterministic_verdict_conflict"}:
            fallback["reason_code"] = str(error)
        return fallback, None

    if "[INTELLIGENT_UI]" not in raw:
        return accepted, None
    try:
        selections = _section(raw, "INTELLIGENT_UI")
        if not isinstance(selections, list) or not 1 <= len(selections) <= CATALOG["selection_limit"]:
            raise ValueError("invalid_ui_selection")
        items = [UISelection.model_validate(item) for item in selections]
        context = state.get("learning_context") or {}
        for item in items:
            if item.evidence_ref not in available:
                raise ValueError("unknown_ui_source")
            if item.component in {"PredictionForm", "ParameterCompare", "RunTraceChart"} and ((context.get("ref") or {}).get("kind") != "root_lab" or item.evidence_ref != ("context:rows" if item.component == "RunTraceChart" else "context:parameters")):
                raise ValueError("incompatible_ui_source")
            if item.component == "ParameterCompare" and context.get("student_claim"):
                raise ValueError("selected_claim_no_preview")
        ui = {"catalog_version": CATALOG["version"], "source_hash": bundle["source_hash"], "status": "validated", "selections": [item.model_dump() for item in items], "context_ref": bundle["context_ref"]}
        return accepted, ui
    except (ValueError, TypeError, ValidationError):
        accepted["ui_status"] = "fallback"
        return accepted, None


def bind_ui(ui: dict, run_id: str, fallback: str) -> dict:
    identity = hashlib.sha256(f"{run_id}:{ui['source_hash']}".encode()).hexdigest()[:24]
    # JSON quoting is language encoding, never executable HTML or script.
    children = [f"c{i}" for i in range(len(ui["selections"]))]
    response = f"root = LearningUI([{', '.join(children)}])\n" + "\n".join(
        f"c{i} = {item['component']}({json.dumps(item['evidence_ref'], ensure_ascii=False)})" for i, item in enumerate(ui["selections"]))
    return {**ui, "artifact_id": f"ui-{identity}", "response": response, "markdown_fallback": fallback}
