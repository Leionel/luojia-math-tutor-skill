"""Tests for R3.3: Goal-directed targeted retrieval and non-fabrication invariants."""
import pytest
from app.knowledge.targeted_retrieval import (
    TargetedCourseRetriever,
    TargetedEvidenceSnippet,
    TargetedRetrievalResult,
    infer_target_goal,
)
from app.tutor.teaching_decision import resolve_decision, source_bundle
import json
from test_learning_workspace import workspace


def test_infer_target_goal_from_pedagogical_gap():
    assert infer_target_goal("ask_missing_condition") == "theorem_conditions"
    assert infer_target_goal(None, missing_conditions=["导数非零"]) == "theorem_conditions"
    assert infer_target_goal("correct_claim") == "counterexample"
    assert infer_target_goal("offer_experiment") == "counterexample"
    assert infer_target_goal(None, claim_status="contradicted") == "counterexample"
    assert infer_target_goal("explain") == "prerequisite"
    assert infer_target_goal(None, claim_status="unknown") == "prerequisite"
    assert infer_target_goal("offer_probe") == "worked_step"
    assert infer_target_goal(None) is None


def test_targeted_retrieval_bounded_to_three_snippets(workspace):
    retriever = TargetedCourseRetriever(course_service=workspace.course)

    # Requesting 10 snippets must still be capped at 3
    result = retriever.retrieve(query="牛顿法初值与收敛条件", goal="theorem_conditions", max_snippets=10)
    assert isinstance(result, TargetedRetrievalResult)
    assert len(result.snippets) <= 3
    assert result.goal == "theorem_conditions"
    assert result.status in {"hit", "low_recall"}
    assert result.snippets[0].id == "targeted:0"
    assert result.snippets[0].scope == "reference_provenance_only"
    assert result.snippets[0].provenance.startswith("course_unit:")
    assert len(result.snippets[0].content_hash) == 64
    assert result.snippets[0].graph_revision == workspace.revision()


def test_targeted_retrieval_obeys_review_boundary_and_zero_budget(workspace):
    for unit in workspace.course.graph_repo.units.values():
        unit.review_status = "pending"
    retriever = TargetedCourseRetriever(workspace.course)
    assert retriever.retrieve("牛顿法", "theorem_conditions").snippets == []
    with pytest.raises(ValueError):
        retriever.retrieve("牛顿法", "theorem_conditions", max_snippets=0)


def test_empty_dataclass_result_does_not_crash_source_bundle():
    assert len(source_bundle({"message": "", "targeted_result": TargetedRetrievalResult(
        goal="theorem_conditions", snippets=[], status="empty", total_recalled=0)})["sources"]) == 1


def test_targeted_root_sources_do_not_pollute_other_subjects(workspace):
    retriever = TargetedCourseRetriever(workspace.course)
    assert retriever.retrieve("贝叶斯定理需要哪些条件？", "theorem_conditions").snippets == []
    assert retriever.retrieve("QR矩阵特征值算法与牛顿法有什么关系？", "prerequisite").snippets == []


def test_real_teacher_receives_targeted_evidence_once_without_second_model_call(workspace, monkeypatch):
    import asyncio
    from app.config import Settings
    from app.tutor.graph import TutorWorkflow
    import app.knowledge.course_service as course_module
    monkeypatch.setattr(course_module, "get_course_service", lambda *args: workspace.course)
    workflow = TutorWorkflow(Settings(teaching_decision_enabled=True), workspace.repository)
    captured = []
    async def generate(state, config, messages, **kwargs):
        captured.append((state, messages))
        return {"metrics": state["metrics"]}
    monkeypatch.setattr(workflow, "_stream_generation", generate)
    result = asyncio.run(workflow.teacher_node({"message": "牛顿法需要哪些局部收敛条件？", "messages": [],
        "mode": "socratic", "hint_level": 0, "intent": "check_student_step",
        "pedagogical_action": "ask_missing_condition"}, {}))
    assert len(captured) == 1
    assert 1 <= result["metrics"]["targeted_snippet_count"] <= 3
    payload = json.loads(captured[0][1][-1]["content"].split("[NODE_CONTEXT]\n")[1].split("\n[/NODE_CONTEXT]")[0])
    assert payload["targeted_evidence"][0]["data"]["content_hash"]
    assert payload["targeted_evidence"][0]["data"]["scope"] == "reference_provenance_only"


def test_targeted_snippets_in_source_bundle_and_accepted_in_decision():
    mock_snippet = TargetedEvidenceSnippet(
        id="targeted:0",
        goal="theorem_conditions",
        title="牛顿法局部收敛定理",
        content="设 f'(x*) != 0 且在根的邻域内二阶可导...",
        chapter_path="第2章",
        review_status="verified",
        provenance="course_unit:newton_local_thm",
        scope="reference_provenance_only",
        content_hash="a" * 64,
        graph_revision="g1",
    )
    state = {
        "message": "牛顿迭代只要初值靠近根就一定二阶收敛。",
        "mode": "socratic",
        "hint_level": 0,
        "intent": "check_student_step",
        "pedagogical_action": "ask_missing_condition",
        "targeted_snippets": [mock_snippet],
    }

    bundle = source_bundle(state)
    target_source = next((s for s in bundle["sources"] if s["id"] == "targeted:0"), None)
    assert target_source is not None
    assert target_source["kind"] == "reference"
    assert target_source["data"]["provenance"] == "course_unit:newton_local_thm"
    assert target_source["data"]["scope"] == "reference_provenance_only"

    # Model makes decision citing targeted:0
    decision_payload = {
        "claim_ref": "claim:current",
        "evidence_refs": ["targeted:0"],
        "known_conditions": ["初值充分靠近根"],
        "missing_conditions": ["导数非零 f'(x*) != 0 与二阶连续可微"],
        "claim_status": "partially_supported",
        "action": "ask_missing_condition",
        "disclosure": "scaffolded",
        "reason": "定理局部收敛需导数非零前提，提示补充条件。",
        "assessments": [],
    }
    raw = (
        "[TEACHING_DECISION]"
        + json.dumps(decision_payload, ensure_ascii=False)
        + "[/TEACHING_DECISION]"
        + "[OUTPUT]请问除了初值充分靠近之外，对根处的导数值有什么前提要求？"
    )

    accepted, _ = resolve_decision(raw, state)
    assert accepted["status"] == "accepted"
    assert "targeted:0" in accepted["evidence_refs"]


def test_targeted_evidence_cannot_certify_unverified_claim():
    mock_snippet = TargetedEvidenceSnippet(
        id="targeted:0",
        goal="theorem_conditions",
        title="牛顿法局部收敛定理",
        content="设 f'(x*) != 0...",
        chapter_path="第2章",
        review_status="verified",
        provenance="course_unit:newton_local_thm",
        scope="reference_provenance_only",
        content_hash="a" * 64,
        graph_revision="g1",
    )
    state = {
        "message": "我的步骤收敛了。",
        "mode": "socratic",
        "hint_level": 0,
        "intent": "check_student_step",
        "pedagogical_action": "confirm_local",
        "targeted_snippets": [mock_snippet],
    }

    # Attempt to mark supported with missing_conditions present -> must be rejected
    decision_payload = {
        "claim_ref": "claim:current",
        "evidence_refs": ["targeted:0"],
        "known_conditions": [],
        "missing_conditions": ["缺少具体函数与初值"],
        "claim_status": "supported",  # Incompatible with missing conditions
        "action": "confirm_local",
        "disclosure": "scaffolded",
        "reason": "检索到了定理就判定学生通过",
        "assessments": [],
    }
    raw = (
        "[TEACHING_DECISION]"
        + json.dumps(decision_payload, ensure_ascii=False)
        + "[/TEACHING_DECISION]"
        + "[OUTPUT]你的步骤完全正确。"
    )

    result, _ = resolve_decision(raw, state)
    assert result["status"] == "fallback"
    assert result["reason_code"] == "unsupported_conditions"


def test_fabricated_targeted_ref_is_rejected():
    state = {
        "message": "这是牛顿法迭代。",
        "mode": "socratic",
        "hint_level": 0,
        "intent": "check_student_step",
        "pedagogical_action": "explain",
        "targeted_snippets": [],
    }
    # citing targeted:99 when not provided
    decision_payload = {
        "claim_ref": "claim:current",
        "evidence_refs": ["targeted:99"],
        "known_conditions": [],
        "missing_conditions": [],
        "claim_status": "unknown",
        "action": "explain",
        "disclosure": "scaffolded",
        "reason": "虚构检索编号",
        "assessments": [],
    }
    raw = (
        "[TEACHING_DECISION]"
        + json.dumps(decision_payload, ensure_ascii=False)
        + "[/TEACHING_DECISION]"
        + "[OUTPUT]我们来看牛顿法的定义。"
    )

    result, _ = resolve_decision(raw, state)
    assert result["status"] == "fallback"
    assert result["reason_code"] == "unknown_evidence_ref"
