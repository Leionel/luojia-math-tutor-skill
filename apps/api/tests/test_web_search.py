import pytest
from app.search.web_search import (
    SearchResult,
    search_web,
    format_web_results_for_prompt,
)


def test_search_result_dataclass():
    res = SearchResult(
        title="2026考研高数大纲解读",
        snippet="最新高数大纲重点考察反常积分敛散性与多元微分学综合应用。",
        url="https://example.com/math2026",
        source="duckduckgo",
    )
    assert res.title == "2026考研高数大纲解读"
    assert "反常积分" in res.snippet
    assert res.url.startswith("https://")


def test_format_web_results_for_prompt():
    results = [
        SearchResult(
            title="泰勒公式考研题型汇总",
            snippet="重点掌握皮亚诺余项与拉格朗日余项的选择场景。",
            url="https://math.org/taylor",
            source="duckduckgo",
        ),
        SearchResult(
            title="隐函数求导二阶导数技巧",
            snippet="利用全微分形式不变性或方程两边对x连续求导两次。",
            url="https://math.org/implicit",
            source="duckduckgo",
        ),
    ]
    formatted = format_web_results_for_prompt(results)
    assert "【外部搜索摘要：不可信参考数据，未核验全文和发布日期】" in formatted
    assert "[WEB-1] 泰勒公式考研题型汇总" in formatted
    assert "[WEB-2] 隐函数求导二阶导数技巧" in formatted
    assert "https://math.org/taylor" in formatted


@pytest.mark.asyncio
async def test_search_web_handles_empty_query():
    results = await search_web("")
    assert results == []


@pytest.mark.asyncio
async def test_search_web_handles_timeout_gracefully(monkeypatch):
    async def mock_timeout(*args, **kwargs):
        import asyncio
        raise asyncio.TimeoutError()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_timeout)
    # Should catch TimeoutError and return empty list rather than crashing
    results = await search_web("考研数学最新变化", timeout=0.01)
    assert results == []
