import asyncio
import time
from unittest.mock import MagicMock

import pytest

from app.memory.repository import Repository
from app.tutor.fast_context import FastContextCollector
from app.tutor.fast_path import VerificationMode, route_fast_path


def make_repository() -> MagicMock:
    repository = MagicMock(spec=Repository)
    repository.list_messages.return_value = []
    repository.list_sessions.return_value = []
    repository.get_mastery.return_value = None
    repository.get_consecutive_errors.return_value = 0
    return repository


def make_state(message: str = "什么是导数？") -> dict:
    route = route_fast_path(message, mode="socratic", subject="calculus")
    return {
        "message": message,
        "session_id": "session-1",
        "user_id": "user-1",
        "subject": "calculus",
        "detected_subject": route.subject,
        "mode": "socratic",
        "requested_hint": False,
        "intent": route.intent,
        "verification_mode": route.verification_mode.value,
    }


@pytest.mark.asyncio
async def test_optional_context_timeout_returns_defaults():
    repository = make_repository()

    async def slow_search(*args, **kwargs):
        await asyncio.sleep(1)
        return []

    collector = FastContextCollector(
        repository=repository,
        timeout_seconds=0.01,
        local_search=slow_search,
    )

    context = await collector.collect(make_state())

    assert context.hits == []
    assert context.document_chunks == []
    assert context.metrics["fast_context_ms"] < 200
    assert context.metrics["context_timed_out"] is True


@pytest.mark.asyncio
async def test_repository_reads_do_not_block_event_loop():
    repository = make_repository()

    def slow_list_messages(session_id):
        time.sleep(0.05)
        return []

    repository.list_messages.side_effect = slow_list_messages
    collector = FastContextCollector(repository=repository)
    ticks = 0

    async def heartbeat():
        nonlocal ticks
        for _ in range(5):
            await asyncio.sleep(0.005)
            ticks += 1

    await asyncio.gather(collector.collect(make_state()), heartbeat())

    assert ticks == 5


@pytest.mark.asyncio
async def test_collect_persists_user_message_and_returns_history():
    repository = make_repository()
    repository.list_messages.return_value = [
        {"role": "user", "content": "上一题"},
        {"role": "assistant", "content": "上一轮回答"},
    ]
    collector = FastContextCollector(repository=repository)

    context = await collector.collect(make_state())

    assert context.history == [
        {"role": "user", "content": "上一题"},
        {"role": "assistant", "content": "上一轮回答"},
    ]
    repository.ensure_user.assert_called_once_with("user-1")
    repository.add_message.assert_called_once_with(
        "session-1",
        "user",
        "什么是导数？",
    )


@pytest.mark.asyncio
async def test_symbolic_route_runs_step_checker():
    repository = make_repository()
    message = "我算 ∫2x dx = x^2 + C，对吗？"
    state = make_state(message)
    assert state["verification_mode"] == VerificationMode.SYMBOLIC.value
    collector = FastContextCollector(repository=repository)

    context = await collector.collect(state)

    assert context.verifier_result.verified is True
    assert context.verifier_result.is_correct is True
    assert context.metrics["symbolic_verify_ms"] >= 0
