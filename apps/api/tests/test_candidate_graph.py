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


def test_approve_preserves_document_provenance(review_setup):
    """An approved unit must still be able to say where it came from.

    The candidate carries an `evidence_ref`, but that stays on the candidate.
    Without mapping these payload fields the canonical unit loses the document
    and section it was extracted from, which breaks the auditability the review
    step exists to provide.
    """
    graph_repo, candidate_mgr, review_service = review_setup
    candidate_mgr.add_candidate(
        candidate_id="NA_DOC_UNIT",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={
            "id": "NA_DOC_UNIT",
            "title": "定理 2.4 Newton 法的局部二次收敛性",
            "type": "theorem",
            "content": "令 x* 为单根，则 Newton 法局部二阶收敛。",
            "chapter_path": ["第 2 章 非线性方程", "2.4 牛顿法"],
            "source_document_id": "doc_656067dd6720",
            "page_start": 88,
            "page_end": 90,
        },
        proposed_by="document_pipeline",
        evidence_ref="document:doc_656067dd6720:定理 2.4",
    )

    res = review_service.review_candidate(
        candidate_id="NA_DOC_UNIT",
        action="approve",
        reviewer_id="teacher_wang",
        review_note="provenance check",
    )
    assert res["status"] == "success"

    unit = graph_repo.get_unit("NA_DOC_UNIT")
    assert unit is not None
    assert unit.chapter_path == ["第 2 章 非线性方程", "2.4 牛顿法"]
    assert unit.source_document_id == "doc_656067dd6720"
    assert unit.page_start == 88
    assert unit.page_end == 90
    assert unit.provenance == "candidate_document_pipeline"
    assert unit.title == "定理 2.4 Newton 法的局部二次收敛性"


def test_support_count_counts_sources_not_extraction_runs(review_setup):
    """Re-running the same document must not make a candidate look corroborated."""
    _, candidate_mgr, _ = review_setup
    payload = {"id": "NA_X", "title": "割线法", "content": "用差商代替导数。"}

    first = candidate_mgr.add_candidate(
        candidate_id="cand_x",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload=payload,
        evidence_ref="document:doc_1:割线法",
    )
    again = candidate_mgr.add_candidate(
        candidate_id="cand_x",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload=payload,
        evidence_ref="document:doc_1:割线法",
    )
    assert again.support_count == 1, "same source must not increment support"

    other = candidate_mgr.add_candidate(
        candidate_id="cand_x",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload=payload,
        evidence_ref="document:doc_2:割线法",
    )
    assert other.support_count == 2
    assert first.candidate_id == other.candidate_id


def test_pending_candidate_payload_is_refreshed_by_a_better_pipeline(review_setup):
    _, candidate_mgr, _ = review_setup
    candidate_mgr.add_candidate(
        candidate_id="cand_y",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={"id": "NA_Y", "title": "定理 2.4", "type": "concept"},
        evidence_ref="document:doc_1:定理 2.4",
    )

    updated = candidate_mgr.add_candidate(
        candidate_id="cand_y",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={
            "id": "NA_Y",
            "title": "定理 2.4",
            "type": "theorem",
            "chapter_path": ["第 2 章", "2.1.3 Newton 法"],
        },
        evidence_ref="document:doc_1:定理 2.4",
    )

    assert updated.payload["type"] == "theorem"
    assert updated.payload["chapter_path"] == ["第 2 章", "2.1.3 Newton 法"]


def test_reviewed_candidate_payload_is_never_overwritten(review_setup):
    """A teacher's decision must survive a later re-extraction."""
    _, candidate_mgr, review_service = review_setup
    candidate_mgr.add_candidate(
        candidate_id="cand_z",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={"id": "NA_Z", "title": "割线法", "type": "algorithm"},
        evidence_ref="document:doc_1:割线法",
    )
    review_service.review_candidate(
        candidate_id="cand_z", action="reject", reviewer_id="teacher_wang"
    )

    after = candidate_mgr.add_candidate(
        candidate_id="cand_z",
        candidate_type=CandidateType.NEW_UNIT.value,
        course_id="numerical_analysis",
        payload={"id": "NA_Z", "title": "割线法", "type": "concept"},
        evidence_ref="document:doc_1:割线法",
    )

    assert after.status == CandidateStatus.REJECTED.value
    assert after.payload["type"] == "algorithm", "reviewed payload must not change"


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
