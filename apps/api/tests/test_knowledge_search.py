import pytest
from app.knowledge.loader import load_knowledge
from app.knowledge.search import (
    get_knowledge_by_refs,
    search_knowledge,
    search_knowledge_local,
)


def test_loads_all_json_knowledge_files():
    items = load_knowledge()
    sources = {item.source_file for item in items}
    assert {"concept_gs.json", "ex.json", "la.json", "proba.json", "Proba_example.json"} <= sources


def test_prerequisite_references_resolve_by_id_or_display_name():
    by_id = get_knowledge_by_refs(["CH1_EX_001"], subject="calculus")
    by_name = get_knowledge_by_refs(["数列极限（定义法证明）"], subject="calculus")

    assert by_id
    assert by_name
    assert by_id[0].id == by_name[0].id


@pytest.mark.asyncio
async def test_search_linear_algebra_determinant():
    hits = await search_knowledge("二阶行列式", "linear_algebra")
    assert hits
    assert any("二阶行列式" in hit.item.concept_zh for hit in hits)


@pytest.mark.asyncio
async def test_search_power_integral_has_calculus_hit():
    hits = await search_knowledge("幂函数积分", "calculus")
    assert hits
    assert any(hit.item.subject == "calculus" for hit in hits)


@pytest.mark.asyncio
async def test_search_conditional_probability():
    hits = await search_knowledge("条件概率", "probability")
    assert hits
    assert any("条件概率" in hit.item.concept_zh or "条件概率" in hit.item.description for hit in hits)


@pytest.mark.asyncio
async def test_local_search_never_creates_embedding(monkeypatch):
    async def fail_embedding(*args, **kwargs):
        raise AssertionError("local search must not call embeddings")

    monkeypatch.setattr(
        "app.llm.openai_compatible.OpenAICompatibleClient.create_embedding",
        fail_embedding,
    )

    hits = await search_knowledge_local("条件概率", "probability")

    assert hits


def test_schema_v1_knowledge_units_contract():
    from app.knowledge.loader import load_knowledge_units
    from app.knowledge.schema import KnowledgeUnit, SourceDocument, KnowledgeRelation

    units = load_knowledge_units(course_id="la_course_101")
    assert len(units) > 0
    unit = units[0]
    assert isinstance(unit, KnowledgeUnit)
    assert unit.schema_version == "v1"
    assert unit.course_id == "la_course_101"
    assert unit.review_status == "verified"

    # Test SourceDocument & KnowledgeRelation contracts
    doc = SourceDocument(id="doc_1", course_id="la_course_101", filename="la_ch1.pdf")
    assert doc.id == "doc_1"
    rel = KnowledgeRelation(source_unit_id="ku_1", target_unit_id="ku_2", relation_type="prerequisite")
    assert rel.relation_type == "prerequisite"

