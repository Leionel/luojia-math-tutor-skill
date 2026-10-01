import pytest
from app.config import Settings
from app.tutor.fast_context import FastContextCollector
from app.memory.repository import Repository
from app.search.web_search import SearchResult


@pytest.mark.asyncio
async def test_fast_context_collects_web_search_when_enabled(monkeypatch, tmp_path):
    repo = Repository(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"))

    async def mock_search_web(query, max_results=3, timeout=1.8):
        return [
            SearchResult(
                title="Mock 考研真题",
                snippet="证明极限存在的常见夹逼准则法。",
                url="https://mock.edu/limit",
                source="mock",
            )
        ]

    monkeypatch.setattr("app.tutor.fast_context.search_web", mock_search_web)

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
