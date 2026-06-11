import pytest
from app.knowledge.loader import load_knowledge
from app.knowledge.search import search_knowledge, search_knowledge_local


def test_loads_all_json_knowledge_files():
    items = load_knowledge()
    sources = {item.source_file for item in items}
    assert {"concept_gs.json", "ex.json", "la.json", "proba.json", "Proba_example.json"} <= sources


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

