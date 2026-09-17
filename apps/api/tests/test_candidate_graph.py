import pytest
from app.knowledge.candidate_graph import CandidateManager, CandidateStatus, CandidateType
from app.knowledge.graph_repository import CourseGraphRepository
from app.knowledge.graph_review import GraphReviewService
from app.knowledge.schema import KnowledgeUnit


@pytest.fixture
def review_setup():
    graph_repo = CourseGraphRepository(course_id="numerical_analysis")
    graph_repo.add_unit(KnowledgeUnit(
        id="NA_NEWTON",
        course_id="numerical_analysis",
        title="牛顿迭代法",
        aliases=["切线法"]
    ))
    candidate_mgr = CandidateManager()
    review_service = GraphReviewService(graph_repo, candidate_mgr)
    return graph_repo, candidate_mgr, review_service


def test_candidate_creation_and_support_count(review_setup):
    _, candidate_mgr, _ = review_setup
    c1 = candidate_mgr.add_candidate(
        candidate_id="cand_secant",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={"title": "割线法 (Secant Method)"},
        proposed_by="student_query_cluster",
        evidence_ref="query_101"
    )
    assert c1.support_count == 1
    assert c1.status == CandidateStatus.PENDING.value

    # Second occurrence increments support count
    c2 = candidate_mgr.add_candidate(
        candidate_id="cand_secant",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={"title": "割线法 (Secant Method)"},
        proposed_by="student_query_cluster",
        evidence_ref="query_102"
    )
    assert c2.support_count == 2
    assert "query_102" in c2.evidence_refs


def test_approve_candidate_into_canonical_graph(review_setup):
    graph_repo, candidate_mgr, review_service = review_setup
    candidate_mgr.add_candidate(
        candidate_id="NA_SECANT",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={"id": "NA_SECANT", "title": "割线法", "type": "algorithm", "content": "用两点割线代替切线避免计算导数。"},
        proposed_by="teacher"
    )

    res = review_service.review_candidate(
        candidate_id="NA_SECANT",
        action="approve",
        reviewer_id="teacher_wang",
        review_note="Approved into root-finding unit."
    )
    assert res["status"] == "success"
    assert res["applied_changes"]["entity_type"] == "unit"
    
    # Verify graph now has this unit
    unit = graph_repo.get_unit("NA_SECANT")
    assert unit is not None
    assert unit.title == "割线法"


def test_merge_candidate_alias_into_existing_unit(review_setup):
    graph_repo, candidate_mgr, review_service = review_setup
    candidate_mgr.add_candidate(
        candidate_id="cand_alias_newton_raphson",
        candidate_type=CandidateType.NEW_ALIAS.value,
        course_id="numerical_analysis",
        payload={"target_id": "NA_NEWTON", "alias": "牛顿-拉弗森法"},
        proposed_by="student_query_cluster"
    )

    res = review_service.review_candidate(
        candidate_id="cand_alias_newton_raphson",
        action="merge",
        reviewer_id="teacher_wang",
        review_note="Merged alias."
    )
    assert res["status"] == "success"
    unit = graph_repo.get_unit("NA_NEWTON")
    assert "牛顿-拉弗森法" in unit.aliases


def test_reject_candidate(review_setup):
    _, candidate_mgr, review_service = review_setup
    candidate_mgr.add_candidate(
        candidate_id="cand_quantum",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={"title": "量子纠缠在求根中的应用"},
        proposed_by="student_query_cluster"
    )

    res = review_service.review_candidate(
        candidate_id="cand_quantum",
        action="reject",
        reviewer_id="teacher_wang",
        review_note="Out of course syllabus scope."
    )
    assert res["status"] == "success"
    cand = candidate_mgr.get_candidate("cand_quantum")
    assert cand.status == CandidateStatus.REJECTED.value
