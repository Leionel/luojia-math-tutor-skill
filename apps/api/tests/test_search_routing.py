import asyncio
import json

import httpx
import pytest

from app.search import web_search as web
from app.search.policy import decide_search, search_query
from app.tutor.fast_path import route_fast_path, VerificationMode
from app.tutor.intent_router import Intent


CLAIM = "讲一下openai证明navier-storke问题得思路？"


def test_claim_routes_to_fact_explanation_and_normalizes_spelling():
    route = route_fast_path(CLAIM, "direct", "auto")
    assert route.intent == Intent.CONCEPT
    assert route.verification_mode == VerificationMode.NONE
    assert not route.requires_policy_fallback
    assert decide_search(CLAIM).enabled
    assert search_query(CLAIM) == "OpenAI Navier Stokes proof"


@pytest.mark.parametrize("question", ["最新数学竞赛新闻", "查一下牛顿法的资料", "OpenAI solved Navier Stokes?", "jacobi猜想被证伪了嘛"])
def test_freshness_or_explicit_request_triggers_search(question):
    assert decide_search(question).enabled
    assert not decide_search(question, "off", True).enabled


def test_normal_proof_and_student_attempt_retain_verification():
    for question in ["证明任意有限群的子群阶数整除群的阶数", "我的证明如下：我算 x=1，帮我检查证明"]:
        assert not decide_search(question).enabled
        assert route_fast_path(question, "socratic", "auto").verification_mode == VerificationMode.LLM
    assert not decide_search("什么是牛顿法").enabled
    assert not decide_search("证明最近邻算法的性质").factual
    assert not decide_search("当前迭代公式为什么这样").factual


@pytest.mark.asyncio
async def test_blocked_ddg_falls_back_to_rss(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    async def get(self, url, **kwargs):
        if "duckduckgo" in url:
            return httpx.Response(202, text="unavailable", request=httpx.Request("GET", url))
        return httpx.Response(200, text="<rss><channel><item><title>Research</title><link>https://example.org/paper</link><description>Abstract</description></item></channel></rss>", request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    report = await web.search_web_report(CLAIM)
    assert report.status == "success"
    assert report.results[0].source == "bing_rss"
    assert report.attempts == [{"provider": "duckduckgo", "status": "error"}, {"provider": "bing_rss", "status": "success"}]


@pytest.mark.asyncio
async def test_tavily_empty_falls_back_and_rejects_unsafe_links(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-only-not-a-real-key")
    async def empty(*args):
        return []
    async def fallback(*args):
        return [web.SearchResult("unsafe", "", "javascript:alert(1)"),
                web.SearchResult("safe", "", "https://example.org/paper")]
    monkeypatch.setattr(web, "_search_tavily", empty)
    monkeypatch.setattr(web, "_search_duckduckgo", fallback)
    report = await web.search_web_report("public query")
    assert len(report.results) == 1
    assert report.results[0].title == "safe"
    assert report.attempts[0]["status"] == "empty"


@pytest.mark.asyncio
async def test_total_deadline_is_observable_and_cancels_search(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    cancelled = asyncio.Event()
    async def slow(*args):
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.set()
    monkeypatch.setattr(web, "_search_duckduckgo", slow)
    report = await web.search_web_report("public query", timeout=0.01)
    assert report.status == "timeout"
    assert cancelled.is_set()
    assert "未完成事实核实" in web.search_status_text(report.to_dict())


@pytest.mark.asyncio
async def test_errors_do_not_leak_keys_or_provider_messages(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    async def failed(*args):
        raise RuntimeError("secret-provider-token")
    monkeypatch.setattr(web, "_search_duckduckgo", failed)
    monkeypatch.setattr(web, "_search_bing_rss", failed)
    report = await web.search_web_report("public query")
    assert report.status == "error"
    assert "secret-provider-token" not in json.dumps(report.to_dict())
