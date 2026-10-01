import asyncio
import json
import pytest
from app.config import Settings
from app.tutor.fast_context import FastContextCollector
from app.memory.repository import Repository
from app.search.web_search import SearchResult, WebSearchReport


@pytest.mark.asyncio
async def test_fast_context_collects_web_search_when_enabled(monkeypatch, tmp_path):
    repo = Repository(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"))

    async def mock_search_web(query, max_results=3, timeout=1.8):
        return WebSearchReport("success", [
            SearchResult(
                title="Mock 考研真题",
                snippet="证明极限存在的常见夹逼准则法。",
                url="https://mock.edu/limit",
                source="mock",
            )
        ])

    monkeypatch.setattr("app.tutor.fast_context.search_web_report", mock_search_web)

    collector = FastContextCollector(repo)
    state = {
        "user_id": "test-user",
        "session_id": "sess-123",
        "message": "考研极限真题求法",
        "web_search": True,
        "reasoning_effort": "high",
        "verification_mode": "heuristic",
    }

    ctx = await collector.collect(state)
    # Check that document_chunks contains the mock search result
    assert any("Mock 考研真题" in chunk for chunk in ctx.document_chunks)
    assert any("https://mock.edu/limit" in chunk for chunk in ctx.document_chunks)
    assert ctx.web_search_report["status"] == "success"
    assert ctx.web_search_report["sources"][0]["id"] == "WEB-1"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["error", "timeout", "empty", "success"])
async def test_search_failure_reaches_prompt_sse_and_persisted_message(monkeypatch, tmp_path, status):
    from unittest.mock import AsyncMock
    from app.tutor.orchestrator import TutorOrchestrator
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'messages.db'}")
    repo = Repository(settings)
    session = repo.create_session("user-1", "auto")["session_id"]
    orchestrator = TutorOrchestrator(settings, repo)
    async def failed(*args, **kwargs):
        return WebSearchReport(status, [SearchResult("Research", "abstract", "https://example.org/paper")] if status == "success" else [])
    monkeypatch.setattr("app.tutor.fast_context.search_web_report", failed)
    prompts = []
    async def stream(messages, **kwargs):
        prompts.extend(messages)
        assert kwargs["enable_search"] is False
        yield {"type": "content", "content": "[OUTPUT]未完成联网核实。"}
    orchestrator.workflow_owner.llm.stream = stream
    verifier = AsyncMock(side_effect=AssertionError("fact question must not enter proof review"))
    orchestrator.workflow_owner.llm.chat_completion = verifier
    events = [event async for event in orchestrator.stream_reply(
        session, "user-1", "讲一下openai证明navier-storke问题得思路？", mode="direct")]
    assert status in next(event for event in events if "event: meta_update" in event)
    verifier.assert_not_called()
    runtime = json.loads(prompts[1]["content"].split("\n", 1)[1].rsplit("\n", 1)[0])
    assert runtime["web_search"]["status"] == status
    assert "不得声称已查证" in runtime["web_search_rule"]
    message = repo.list_messages(session)[-1]
    assert message["learning_meta"]["web_search"]["status"] == status
    assert message["learning_meta"]["verification_kind"] == "none"
    assert message["learning_meta"]["concepts"] == []
    assert "推理审查未返回有效状态" not in message["content"]


@pytest.mark.asyncio
async def test_explicit_off_does_not_call_search(monkeypatch, tmp_path):
    from unittest.mock import AsyncMock
    from test_orchestrator import make_orchestrator, QuickWorkflow
    # Verify request policy separately from the collector's network gate.
    from app.search.policy import decide_search
    decision = decide_search("OpenAI证明Navier Stokes了？", "off", True)
    mock = AsyncMock(side_effect=AssertionError("network must stay off"))
    monkeypatch.setattr("app.tutor.fast_context.search_web_report", mock)
    repo = Repository(Settings(database_url=f"sqlite:///{tmp_path / 'off.db'}"))
    ctx = await FastContextCollector(repo).collect({"user_id": "user", "session_id": "off",
        "message": "OpenAI证明Navier Stokes了？", "web_search": decision.enabled,
        "web_search_reason": decision.reason, "external_fact_question": True})
    assert ctx.web_search_report["status"] == "disabled"
    assert ctx.web_search_report["reason"] == "explicit_off"
    mock.assert_not_called()
    workflow = QuickWorkflow()
    orchestrator = make_orchestrator(workflow)
    states = []
    original = workflow.ainvoke
    async def capture(state, config):
        states.append(state)
        return await original(state, config)
    workflow.ainvoke = capture
    _ = [event async for event in orchestrator.stream_reply("off", "user", "OpenAI证明Navier Stokes了？", web_search=True, web_search_mode="off")]
    assert states[0]["web_search"] is False


@pytest.mark.asyncio
async def test_search_has_separate_budget_and_is_cancelled_with_request(monkeypatch, tmp_path):
    entered = asyncio.Event()
    cancelled = asyncio.Event()
    async def slow(*args, **kwargs):
        entered.set()
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.set()
    monkeypatch.setattr("app.tutor.fast_context.search_web_report", slow)
    repo = Repository(Settings(database_url=f"sqlite:///{tmp_path / 'cancel.db'}"))
    state = {"user_id": "user", "session_id": "cancel", "message": "新闻",
             "web_search": True, "external_fact_question": True}
    task = asyncio.create_task(FastContextCollector(repo, timeout_seconds=0.001).collect(state))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cancelled.is_set()

    async def delayed(*args, **kwargs):
        await asyncio.sleep(0.025)
        return WebSearchReport("success", [SearchResult("news", "abstract", "https://example.org/news")])
    monkeypatch.setattr("app.tutor.fast_context.search_web_report", delayed)
    ctx = await FastContextCollector(repo, timeout_seconds=0.001).collect(state)
    assert ctx.web_search_report["status"] == "success"
