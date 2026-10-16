from copy import deepcopy
import pytest
from fastapi.testclient import TestClient

from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.knowledge.case_schema import CaseDecision, TeachingCase
from app.knowledge.schema import KnowledgeUnit
from app.knowledge.boundary import BoundaryPolicy
from app.knowledge.evidence_builder import CourseEvidenceBuilder


@pytest.fixture
def service():
    return CourseService(store=CourseStore())


@pytest.mark.parametrize("query,expected", [
    ("Under what assumptions is bisection applicable?", "CASE_BISECTION_REQUIREMENTS"),
    ("牛顿法求重根为什么变慢？", "CASE_NEWTON_MULTIPLE_ROOT"),
    ("State a sufficient condition for convergence of fixed-point iteration.", "CASE_FIXED_POINT_CONTRACTION"),
    ("Use Taylor expansion to derive the Newton formula.", "CASE_NEWTON_DERIVATION"),
])
def test_shared_bilingual_metadata_recall(service, query, expected):
    result = service.case_matcher.match(query)
    assert result.matched_case_id == expected
    assert result.candidate_cases[0]["case_id"] == expected
    assert result.unit_candidates


def test_context_changes_task_not_teaching_mode(service):
    q = "Newton derivative near zero guard"
    result = service.case_matcher.match(q, context={"task_mode": "code_task"})
    assert result.matched_case_id == "CASE_NEWTON_CODE_UPDATE"
    assert service.case_matcher.match(q, context={"task_mode": "guided"}).to_dict() == service.case_matcher.match(q).to_dict()


def test_ambiguous_task_asks_instead_of_inventing_an_algorithm(service):
    result = service.case_matcher.match("某个迭代算法不对，我没有具体步骤")
    assert result.decision == CaseDecision.UNCERTAIN
    assert result.matched_case_id is None
    assert result.clarification_question


def test_missing_diagnostic_inputs_are_not_a_verified_diagnosis(service):
    result = service.case_matcher.match("Newton does not converge.")
    assert result.clarification_question
    assert "尚不能定位错误" in result.clarification_question


@pytest.mark.parametrize("q", ["QR迭代求矩阵特征值", "Romberg积分的稳定性", "Brent法求根", "Newton雅可比求非线性方程组"])
def test_noncanonical_topics_do_not_enter_scalar_root_cases(service, q):
    result = service.case_matcher.match(q)
    assert result.decision == CaseDecision.NEW_CASE
    assert result.matched_case_id is None


def test_unreviewed_cases_and_unknown_course_are_excluded(service):
    service.graph_repo.add_case(TeachingCase("DRAFT", "numerical_analysis", "未知算法极端精确问法", review_status="draft", accepted_variants=["未知算法极端精确问法"]))
    assert service.case_matcher.match("未知算法极端精确问法").matched_case_id != "DRAFT"
    result = service.case_matcher.match("牛顿法为什么初值选不好会发散", course_id="another_course")
    assert not result.candidate_cases and not result.unit_candidates and result.matched_case_id is None


def test_units_are_recalled_without_a_teaching_case_and_respect_review_boundary(service):
    for uid, status, scope in [("ALLOWED", "verified", "core"), ("DRAFT", "draft", "core"), ("EXTERNAL", "verified", "external"), ("EXT", "verified", "extension")]:
        service.graph_repo.add_unit(KnowledgeUnit(uid, "numerical_analysis", title="自定义测试标题 zetaquux", review_status=status),
                                   BoundaryPolicy("numerical_analysis", uid, scope_level=scope))
    ids = [row["unit_id"] for row in service.graph_repo.search_units("zetaquux")]
    assert ids == ["ALLOWED"]
    result = service.case_matcher.match("zetaquux")
    assert result.matched_case_id is None
    assert result.unit_candidates[0]["unit_id"] == "ALLOWED"


def test_endpoint_evidence_builder_and_offline_evaluator_use_identical_ranking(service, monkeypatch):
    from app.main import app
    import app.api.routes_courses as routes
    import app.knowledge.evidence_builder as builder_module
    monkeypatch.setattr(routes, "get_course_service", lambda _: service)
    monkeypatch.setattr(builder_module, "get_course_service", lambda _: service)
    query = "How many bisections guarantee midpoint error below a tolerance?"
    actual = service.case_matcher.match(query).to_dict()
    import importlib.util
    from pathlib import Path
    evaluator_path = Path(__file__).resolve().parents[3] / "evaluation" / "evaluate_case_benchmark.py"
    spec = importlib.util.spec_from_file_location("offline_case_evaluator", evaluator_path)
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    offline_matcher, _ = evaluator._load_matcher()
    assert offline_matcher.match(query).to_dict() == actual
    endpoint = TestClient(app).post("/api/courses/numerical_analysis/cases/match", json={"query": query}).json()
    pack = CourseEvidenceBuilder().build_evidence_pack(query)
    # Public delivery redacts probe answers; ranking still shares the exact
    # production/evaluator implementation and must remain identical.
    for key in ("decision", "matched_case_id", "confidence", "candidate_cases",
                "concept_anchor_ids", "difference_axes", "unit_candidates",
                "review_required", "clarification_question", "reason"):
        assert endpoint[key] == actual[key]
    assert endpoint["matched_case"]["case_id"] == actual["matched_case_id"]
    assert "correct_answer" not in (endpoint["diagnostic_probe"] or {})
    from app.auth import Principal
    assert routes._public_case(actual["matched_case"], Principal("teacher", True, "teacher")) == actual["matched_case"]
    assert pack.retrieval_trace["case_candidates"] == actual["candidate_cases"]
    assert pack.retrieval_trace["unit_candidates"] == actual["unit_candidates"]
    assert pack.matched_case["case_id"] == actual["matched_case_id"]
    assert pack.citations and pack.condition_details
    assert all(d["verification_status"] == "not_checked" for d in pack.condition_details)
    assert any(d["kind"] == "case_declared_condition" for d in pack.condition_details)


def test_blocked_and_draft_units_never_enter_teaching_hits(service, monkeypatch):
    import app.knowledge.evidence_builder as module
    monkeypatch.setattr(module, "get_course_service", lambda _: service)
    service.graph_repo.units["NA_NEWTON"].review_status = "draft"
    service.graph_repo.boundary_checker.policies["MATH_TAYLOR"].scope_level = "external"
    pack = CourseEvidenceBuilder().build_evidence_pack("牛顿法公式怎么推导？")
    ids = {h.item.id for h in pack.graph_hits}
    assert "NA_NEWTON" not in ids and "MATH_TAYLOR" not in ids
    assert all(h.item.id in service.graph_repo.units for h in pack.graph_hits)


def test_approved_alias_reindexes_immediately_and_after_restart(tmp_path):
    path = str(tmp_path / "store.db")
    svc = CourseService(store=CourseStore(path))
    svc.candidate_mgr.add_candidate("alias", "new_alias", "numerical_analysis", {"target_id": "CASE_NEWTON_INITIAL_VALUE", "variant": "quux-test 迭代排查"})
    svc.review_service.review_candidate("alias", "merge")
    assert svc.case_matcher.match("quux-test 迭代排查").matched_case_id == "CASE_NEWTON_INITIAL_VALUE"
    svc.store.close()
    restarted = CourseService(store=CourseStore(path))
    assert restarted.case_matcher.match("quux-test 迭代排查").matched_case_id == "CASE_NEWTON_INITIAL_VALUE"
    restarted.store.close()
