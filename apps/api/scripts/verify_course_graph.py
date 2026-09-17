"""
Standalone verification script for Luojia Math Tutor Course Graph & Teaching Case System.
Runs without third-party dependencies using Python's built-in unittest / assertion runner.
"""
import sys
from pathlib import Path

# Add apps/api to sys.path
api_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(api_root))

from app.knowledge.case_schema import (
    CaseDecision,
    TeachingCase,
    TaskType,
    DisclosurePolicy,
)
from app.knowledge.case_repository import TeachingCaseRepository
from app.knowledge.case_matcher import TeachingCaseMatcher
from app.knowledge.boundary import BoundaryChecker, BoundaryPolicy, ScopeLevel
from app.knowledge.candidate_graph import (
    CandidateManager,
    CandidateStatus,
    CandidateType,
)
from app.knowledge.graph_repository import CourseGraphRepository
from app.knowledge.graph_review import GraphReviewService
from app.knowledge.student_overlay import StudentOverlayStore
from app.knowledge.schema import KnowledgeUnit, KnowledgeRelation


def test_course_pack_loading():
    print("Testing Course Pack loading...")
    repo_root = api_root.parents[1]
    pack_path = repo_root / "data" / "course_packs" / "numerical_analysis_root_finding.json"
    assert pack_path.exists(), f"Course pack not found at {pack_path}"

    import json
    with open(pack_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph_repo = CourseGraphRepository(course_id="numerical_analysis")
    graph_repo.load_from_course_pack(data)

    assert len(graph_repo.units) >= 20, f"Expected >=20 units, got {len(graph_repo.units)}"
    assert len(graph_repo.relations) >= 15, f"Expected >=15 relations, got {len(graph_repo.relations)}"
    assert graph_repo.case_repo.count() >= 10, f"Expected >=10 cases, got {graph_repo.case_repo.count()}"

    # Check key units
    assert "NA_NEWTON" in graph_repo.units
    assert "NA_BISECTION" in graph_repo.units
    assert "MATH_IVT" in graph_repo.units
    assert "NA_COUNTER_NEWTON_CYCLE" in graph_repo.units

    print(f"  [PASS] Successfully loaded {len(graph_repo.units)} units, {len(graph_repo.relations)} relations, {graph_repo.case_repo.count()} cases.")
    return graph_repo


def test_boundary_constraints(graph_repo):
    print("Testing Course Boundary constraints...")
    checker = graph_repo.boundary_checker

    assert checker.get_scope_level("NA_NEWTON") == ScopeLevel.CORE
    assert checker.get_scope_level("MATH_IVT") == ScopeLevel.PREREQUISITE
    assert checker.get_scope_level("NA_COUNTER_NEWTON_CYCLE") == ScopeLevel.EXTENSION

    # Can expand core at depth 1
    allowed, _ = checker.can_expand("NA_NEWTON", current_depth=1)
    assert allowed is True

    # Cannot expand extension without permission
    allowed_ext, _ = checker.can_expand("NA_COUNTER_NEWTON_CYCLE", current_depth=1, allow_extension=False)
    assert allowed_ext is False

    # Filter units
    uids = ["NA_NEWTON", "MATH_IVT", "NA_COUNTER_NEWTON_CYCLE"]
    core_only = checker.filter_units(uids, allow_extension=False, allow_prerequisite=False)
    assert core_only == ["NA_NEWTON"]

    prereq_allowed = checker.filter_units(uids, allow_extension=False, allow_prerequisite=True)
    assert prereq_allowed == ["NA_NEWTON", "MATH_IVT"]

    print("  [PASS] Boundary constraints strictly enforced.")


def test_subgraph_typed_expansion(graph_repo):
    print("Testing Subgraph typed expansion...")
    units, relations = graph_repo.get_subgraph(
        center_unit_ids=["NA_NEWTON"],
        max_depth=1,
        task_mode="convergence_analysis",
        allow_extension=True
    )
    unit_ids = {u.id for u in units}
    assert "NA_NEWTON" in unit_ids
    assert len(unit_ids) >= 2
    assert len(relations) >= 1
    print(f"  [PASS] Subgraph expansion around NA_NEWTON yielded {len(unit_ids)} units and {len(relations)} relations.")


def test_teaching_case_matching(graph_repo):
    print("Testing Teaching Case matching engine...")
    matcher = TeachingCaseMatcher(graph_repo.case_repo)

    # 1. Exact / near query matching
    res1 = matcher.match("牛顿法为什么初值选不好会发散")
    assert res1.matched_case_id == "CASE_NEWTON_INITIAL_VALUE", f"Got {res1.matched_case_id}"
    assert res1.decision in (CaseDecision.SAME_CASE, CaseDecision.VARIANT_OF_CASE)
    assert res1.confidence >= 0.5
    assert res1.diagnostic_probe is not None
    print(f"  [PASS] Query 1 matched: {res1.matched_case_id} ({res1.decision.value}, conf={res1.confidence})")

    # 2. Condition variant query matching
    res2 = matcher.match("重根情况下牛顿法的收敛阶是多少？")
    assert res2.matched_case_id == "CASE_NEWTON_MULTIPLE_ROOT", f"Got {res2.matched_case_id}"
    print(f"  [PASS] Query 2 matched: {res2.matched_case_id} ({res2.decision.value}, conf={res2.confidence})")

    # 3. Residual vs error
    res3 = matcher.match("残差很小是不是就说明方程算对了？")
    assert res3.matched_case_id == "CASE_RESIDUAL_VS_ERROR", f"Got {res3.matched_case_id}"
    print(f"  [PASS] Query 3 matched: {res3.matched_case_id} ({res3.decision.value}, conf={res3.confidence})")

    # 4. Unknown query out of syllabus
    res4 = matcher.match("量子力学谐振子波函数能量本征值怎么计算？")
    assert res4.decision == CaseDecision.NEW_CASE
    assert res4.review_required is True
    print(f"  [PASS] Query 4 correctly flagged NEW_CASE with review_required=True")


def test_candidate_evolution_and_review(graph_repo):
    print("Testing Candidate Evolution & Teacher Review...")
    candidate_mgr = CandidateManager()
    review_service = GraphReviewService(graph_repo, candidate_mgr)

    cand = candidate_mgr.add_candidate(
        candidate_id="NA_SECANT_METHOD",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={
            "id": "NA_SECANT_METHOD",
            "title": "割线法 (Secant Method)",
            "type": "algorithm",
            "content": "使用两点差商近似切线斜率以避免显式导数计算。"
        },
        proposed_by="student_query_cluster",
        evidence_ref="query_cluster_77"
    )
    assert cand.support_count == 1
    assert cand.status == CandidateStatus.PENDING.value

    # Approve into canonical graph
    res = review_service.review_candidate(
        candidate_id="NA_SECANT_METHOD",
        action="approve",
        reviewer_id="prof_wang",
        review_note="Approved into numerical analysis syllabus."
    )
    assert res["status"] == "success"
    approved_unit = graph_repo.get_unit("NA_SECANT_METHOD")
    assert approved_unit is not None
    assert approved_unit.title == "割线法 (Secant Method)"
    print("  [PASS] Candidate approved and verified inside canonical graph.")


def test_student_overlay_reducer():
    print("Testing Student Overlay event reducer...")
    store = StudentOverlayStore()
    student_id = "test_student_42"
    course_id = "numerical_analysis"

    # Initial state
    unit_st = store.get_unit_state(student_id, course_id, "NA_NEWTON")
    assert unit_st.mastery_estimate == 0.5
    assert unit_st.independent_evidence_count == 0

    # Record independent success event
    store.record_process_event(
        event_id="evt_01",
        student_id=student_id,
        course_id=course_id,
        unit_ids=["NA_NEWTON"],
        case_id="CASE_NEWTON_INITIAL_VALUE",
        event_type="attempt",
        is_independent=True,
        is_success=True
    )

    overlay = store.get_course_overlay(student_id, course_id)
    assert overlay["units"]["NA_NEWTON"]["independent_evidence_count"] == 1
    assert overlay["units"]["NA_NEWTON"]["mastery_estimate"] > 0.5
    assert overlay["cases"]["CASE_NEWTON_INITIAL_VALUE"]["latest_outcome"] == "success"
    assert overlay["cases"]["CASE_NEWTON_INITIAL_VALUE"]["independent_transfer_status"] == "verified"
    print("  [PASS] Student Overlay successfully reduced process events into mastery state.")


def test_react_flow_export(graph_repo):
    print("Testing React Flow export...")
    rf = graph_repo.export_react_flow()
    assert "nodes" in rf
    assert "edges" in rf
    assert rf["total_nodes"] >= 20
    assert rf["total_edges"] >= 15

    node_types = {n["data"]["unit_type"] for n in rf["nodes"]}
    assert "algorithm" in node_types
    assert "theorem" in node_types
    assert "concept" in node_types

    print(f"  [PASS] Exported {rf['total_nodes']} React Flow nodes and {rf['total_edges']} edges.")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Course Graph & Teaching Case Standalone Test Suite")
    print("=" * 60)
    repo = test_course_pack_loading()
    test_boundary_constraints(repo)
    test_subgraph_typed_expansion(repo)
    test_teaching_case_matching(repo)
    test_candidate_evolution_and_review(repo)
    test_student_overlay_reducer()
    test_react_flow_export(repo)
    print("=" * 60)
    print("ALL STANDALONE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
