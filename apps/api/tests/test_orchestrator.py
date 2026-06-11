import asyncio
import json
from contextlib import suppress
from unittest.mock import MagicMock

import pytest

from app.memory.repository import Repository
from app.tutor.orchestrator import TutorOrchestrator, sse


def make_orchestrator(workflow) -> TutorOrchestrator:
    orchestrator = TutorOrchestrator.__new__(TutorOrchestrator)
    orchestrator.workflow = workflow
    orchestrator.repository = MagicMock(spec=Repository)
    orchestrator.repository.add_message.return_value = "message-1"
    orchestrator.workflow_owner = MagicMock()
    return orchestrator


class QuickWorkflow:
    async def ainvoke(self, state, config):
        await config["configurable"]["on_thinking"](
            sse("meta", {"route": "teacher"})
        )
        await config["configurable"]["on_token"](
            sse("message", {"content": "回答"})
        )
        return {
            **state,
            "final_output": "回答",
            "thinking_chain": "",
            "metrics": {
                **state["metrics"],
                "llm_call_count": 1,
                "route": "teacher",
            },
        }


def parse_event(event: str) -> tuple[str, dict]:
    lines = event.strip().splitlines()
    name = lines[0].removeprefix("event: ")
    data = json.loads(lines[1].removeprefix("data: "))
    return name, data


@pytest.mark.asyncio
async def test_done_event_contains_latency_and_call_metrics():
    orchestrator = make_orchestrator(QuickWorkflow())

    events = [
        parse_event(event)
        async for event in orchestrator.stream_reply(
            session_id="session-1",
            user_id="user-1",
            message="什么是导数？",
            subject="calculus",
        )
    ]

    done = next(data for name, data in events if name == "done")
    assert done["metrics"]["opening_ms"] < 150
    assert done["metrics"]["total_ms"] >= done["metrics"]["opening_ms"]
    assert done["metrics"]["llm_call_count"] == 1
    assert done["metrics"]["route"] == "teacher"


@pytest.mark.asyncio
async def test_persisted_assistant_message_includes_visible_opening():
    orchestrator = make_orchestrator(QuickWorkflow())

    async for _ in orchestrator.stream_reply(
        session_id="session-1",
        user_id="user-1",
        message="什么是导数？",
        subject="calculus",
    ):
        pass

    persisted_content = orchestrator.repository.add_message.call_args.args[2]
    assert persisted_content.startswith("我们先抓住这个概念")
    assert persisted_content.endswith("回答")


@pytest.mark.asyncio
async def test_twenty_concurrent_openings_arrive_without_graph_delay():
    class SlowWorkflow:
        async def ainvoke(self, state, config):
            await asyncio.sleep(1)
            return state

    orchestrator = make_orchestrator(SlowWorkflow())

    async def first_event(index: int) -> str:
        stream = orchestrator.stream_reply(
            session_id=f"session-{index}",
            user_id=f"user-{index}",
            message="解释导数",
            subject="calculus",
        )
        event = await asyncio.wait_for(anext(stream), timeout=0.15)
        await stream.aclose()
        return event

    events = await asyncio.gather(*(first_event(i) for i in range(20)))

    assert all(event.startswith("event: opening") for event in events)


@pytest.mark.asyncio
async def test_cancelling_stream_cancels_graph_task():
    started = asyncio.Event()
    cancelled = asyncio.Event()

    class BlockingWorkflow:
        async def ainvoke(self, state, config):
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

    orchestrator = make_orchestrator(BlockingWorkflow())
    stream = orchestrator.stream_reply(
        session_id="session-1",
        user_id="user-1",
        message="解释导数",
        subject="calculus",
    )
    await anext(stream)
    pending_event = asyncio.create_task(anext(stream))
    await asyncio.wait_for(started.wait(), timeout=0.2)

    pending_event.cancel()
    with suppress(asyncio.CancelledError):
        await pending_event

    await asyncio.wait_for(cancelled.wait(), timeout=0.2)


@pytest.mark.asyncio
async def test_semantic_enrichment_is_scheduled_after_current_turn():
    orchestrator = make_orchestrator(QuickWorkflow())

    events = [
        parse_event(event)
        async for event in orchestrator.stream_reply(
            session_id="session-1",
            user_id="user-1",
            message="解释导数",
            subject="calculus",
            user_api_key="user-key",
        )
    ]

    assert any(name == "done" for name, _ in events)
    orchestrator.workflow_owner.schedule_semantic_enrichment.assert_called_once_with(
        "解释导数",
        "calculus",
        "user-key",
    )
