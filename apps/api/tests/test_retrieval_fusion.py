"""Retrieval fusion and prompt injection budget.

Covers the two defects that made the Course Graph 2.0 path effectively
unranked: every graph hit carried the constant score 85, and the course graph
and the hybrid retriever were mutually exclusive rather than fused.
"""

import asyncio

import pytest

from app.knowledge.evidence_builder import CourseEvidenceBuilder
from app.knowledge.schema import EvidencePack, KnowledgeHit, KnowledgeItem
from app.memory.repository import Repository
from app.config import Settings
from app.tutor.fast_context import (
    _LOCAL_SEARCH_BUDGET_SECONDS,
    FastContextCollector,
    fuse_evidence_packs,
    fuse_hits,
)
from app.tutor.prompt_builder import _HITS_CHAR_BUDGET, _hits_text


def _hit(item_id: str, score: int, description: str = "", title: str | None = None) -> KnowledgeHit:
    return KnowledgeHit(
        item=KnowledgeItem(
            id=item_id,
            subject="numerical_analysis",
            source_file="course_pack",
            concept_zh=title or item_id,
            prerequisite=[],
            description=description,
            intuitive_explanation="",
            solution="",
        ),
        score=score,
    )


def test_fusion_ranks_by_reciprocal_rank_not_raw_score() -> None:
    """A constant 85 must not lose to a 20000-scale RRF score, and vice versa.

    The two retrievers emit incomparable score scales, so merging on raw scores
    would let whichever list happened to use bigger numbers win outright.
    """
    course = [_hit("shared", 85), _hit("course_only", 60)]
    hybrid = [_hit("shared", 20000), _hit("hybrid_only", 19000)]

    fused = fuse_hits(course, hybrid)

    assert [h.item.id for h in fused] == ["shared", "course_only", "hybrid_only"]
    scores = [h.score for h in fused]
    assert scores == sorted(scores, reverse=True)


def test_fusion_prefers_the_richer_wrapper_for_the_same_unit() -> None:
    lean = _hit("unit", 20000, description="短")
    rich = _hit("unit", 85, description="完整的定理陈述与证明内容", title="牛顿迭代法的收敛性")

    fused = fuse_hits([lean], [rich])

    assert len(fused) == 1
    assert fused[0].item.description == rich.item.description
    assert fused[0].item.concept_zh == "牛顿迭代法的收敛性"


def test_fusing_a_single_list_preserves_its_order() -> None:
    ranked = [_hit("a", 90), _hit("b", 80), _hit("c", 70)]

    assert [h.item.id for h in fuse_hits(ranked)] == ["a", "b", "c"]


def test_fuse_evidence_packs_preserves_course_metadata() -> None:
    course = EvidencePack(
        query_scope={"course_id": "numerical_analysis"},
        direct_hits=[],
        graph_hits=[_hit("anchor", 100)],
        matched_case={"case_id": "CASE_NEWTON"},
        concept_anchors=["anchor"],
        boundary_decision={"level": "core"},
        teaching_hints=[{"type": "probe"}],
    )
    local = EvidencePack(direct_hits=[_hit("kb_unit", 20000)], graph_hits=[])

    fused = fuse_evidence_packs(course, local)

    assert fused is not None
    assert fused.matched_case == {"case_id": "CASE_NEWTON"}
    assert fused.concept_anchors == ["anchor"]
    assert fused.boundary_decision == {"level": "core"}
    assert fused.teaching_hints == [{"type": "probe"}]
    # One ranked list, not two lists the caller has to concatenate.
    assert fused.graph_hits == []
    assert {h.item.id for h in fused.direct_hits} == {"anchor", "kb_unit"}


def test_fuse_evidence_packs_handles_a_missing_side() -> None:
    local = EvidencePack(direct_hits=[_hit("kb_unit", 20000)], graph_hits=[])

    assert fuse_evidence_packs(None, None) is None
    assert [h.item.id for h in fuse_evidence_packs(None, local).direct_hits] == ["kb_unit"]
    assert fuse_evidence_packs(local, None) is not None


@pytest.mark.asyncio
async def test_slow_hybrid_search_does_not_starve_the_course_pack(tmp_path) -> None:
    """The hybrid retriever may call an embedding API; it must not take the
    course-graph result down with it when it exceeds its sub-budget."""
    course_pack = EvidencePack(
        direct_hits=[],
        graph_hits=[_hit("anchor", 100)],
        concept_anchors=["anchor"],
    )

    async def slow_search(query, subject, limit):
        await asyncio.sleep(_LOCAL_SEARCH_BUDGET_SECONDS * 5)
        return EvidencePack(direct_hits=[_hit("late", 20000)], graph_hits=[])

    collector = FastContextCollector(
        repository=Repository(Settings(database_url=f"sqlite:///{tmp_path / 'fusion.db'}")),
        local_search=slow_search,
    )

    async def fake_course_pack(state):
        return course_pack

    collector._course_graph_pack = fake_course_pack

    pack, elapsed_ms = await collector._collect_local_hits({"message": "牛顿法为什么收敛"})

    assert pack is not None
    assert [h.item.id for h in pack.direct_hits] == ["anchor"]
    assert elapsed_ms < _LOCAL_SEARCH_BUDGET_SECONDS * 3 * 1000


@pytest.mark.asyncio
async def test_both_retrievers_contribute_when_both_are_fast(tmp_path) -> None:
    course_pack = EvidencePack(
        direct_hits=[], graph_hits=[_hit("anchor", 100)], concept_anchors=["anchor"]
    )

    async def fast_search(query, subject, limit):
        return EvidencePack(direct_hits=[_hit("kb_unit", 20000)], graph_hits=[])

    collector = FastContextCollector(
        repository=Repository(Settings(database_url=f"sqlite:///{tmp_path / 'fusion.db'}")),
        local_search=fast_search,
    )

    async def fake_course_pack(state):
        return course_pack

    collector._course_graph_pack = fake_course_pack

    pack, _ = await collector._collect_local_hits({"message": "牛顿法为什么收敛"})

    assert {h.item.id for h in pack.direct_hits} == {"anchor", "kb_unit"}


def test_hits_text_gives_the_top_hit_more_than_the_old_240_char_cut() -> None:
    long_unit = "牛顿迭代法的局部二次收敛性。" * 80
    text = _hits_text([_hit("theorem", 100, description=long_unit, title="定理 2.4")])

    assert len(text) > 240
    assert "定理 2.4" in text


def test_hits_text_stays_within_budget_and_reports_omission() -> None:
    hits = [
        _hit(f"unit_{i}", 1000 - i, description=f"第 {i} 个知识单元的完整内容。" * 40)
        for i in range(20)
    ]

    text = _hits_text(hits)
    body = "\n".join(line for line in text.splitlines() if "未注入" not in line)

    assert len(body) <= _HITS_CHAR_BUDGET + 400  # one hit may straddle the boundary
    assert "未注入" in text, "elided hits must be visible, not silently dropped"


def test_hits_text_without_hits_is_explicit() -> None:
    assert _hits_text([]) == "未命中本地知识库条目。"


def test_course_graph_hits_are_scored_by_position_not_a_constant() -> None:
    """Anchored units must outrank 1-hop neighbours pulled in by expansion."""
    builder = CourseEvidenceBuilder(course_id="numerical_analysis")
    pack = builder.build_evidence_pack(query="牛顿迭代法为什么能够收敛？")

    if not pack.graph_hits:
        pytest.skip("course pack produced no graph hits for this query")

    scores = [hit.score for hit in pack.graph_hits]
    assert len(set(scores)) > 1, "graph hits must not all tie"
    assert scores == sorted(scores, reverse=True), "graph hits must come pre-ranked"
