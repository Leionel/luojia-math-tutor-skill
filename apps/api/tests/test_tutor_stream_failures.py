import httpx
import pytest
from app.llm.completion_protocol import ModelCompletionError
from test_orchestrator import make_orchestrator, parse_event


@pytest.mark.asyncio
@pytest.mark.parametrize("failure,code", [
    (httpx.HTTPStatusError("private vendor body", request=httpx.Request("POST", "https://example.org"), response=httpx.Response(401)), "model_auth_failed"),
    (httpx.ReadTimeout("private vendor body"), "model_timeout"),
    (httpx.ConnectError("private vendor body"), "model_unreachable"),
])
async def test_stream_errors_are_typed_safe_persisted_and_not_done(failure, code):
    class Failed:
        async def ainvoke(self, state, config): raise failure
    runner = make_orchestrator(Failed())
    events = [parse_event(e) async for e in runner.stream_reply("session-1", "student-1", "画膜振动")]
    assert not any(name == "done" for name, data in events)
    error = next(data for name, data in events if name == "error")
    assert error["code"] == code and "private" not in error["message"]
    meta = runner.repository.add_message.call_args.args[-1]
    assert not meta["verified"] and meta["is_correct"] is None and meta["error"]["code"] == code


@pytest.mark.asyncio
async def test_error_frame_survives_error_persistence_failure():
    class Failed:
        async def ainvoke(self, state, config): raise httpx.ReadTimeout("timeout")
    runner = make_orchestrator(Failed())
    runner.repository.add_message.side_effect = RuntimeError("disk failed")
    events = [parse_event(e) async for e in runner.stream_reply("session-1", "student-1", "画膜振动")]
    assert events[-1][0] == "error" and events[-1][1]["code"] == "model_timeout"


@pytest.mark.asyncio
@pytest.mark.parametrize("code", ["model_stream_incomplete", "model_output_truncated", "model_empty_output", "model_not_configured"])
async def test_completion_protocol_failures_are_not_successful_answers(code):
    class Failed:
        async def ainvoke(self, state, config):
            raise ModelCompletionError(code)
    runner = make_orchestrator(Failed())
    events = [parse_event(e) async for e in runner.stream_reply("session-1", "student-1", "什么是导数")]
    assert events[-1][0] == "error" and events[-1][1]["code"] == code
    assert not any(name == "done" for name, _ in events)
    assert not any(name == "message" for name, _ in events)
    meta = runner.repository.add_message.call_args.args[-1]
    assert meta["error"]["code"] == code and not meta["verified"]


@pytest.mark.asyncio
async def test_clarification_persists_history_but_no_assessment_or_enrichment():
    class Clarify:
        async def ainvoke(self, state, config):
            return {**state, "awaiting_intent_clarification": True, "final_output": "请补充任务。"}
    runner = make_orchestrator(Clarify())
    events = [parse_event(e) async for e in runner.stream_reply("session-1", "student-1", "？")]
    meta = next(data for name, data in events if name == "meta_update")
    assert meta["intent"] == "intent_clarification" and not meta["verified"]
    assert meta["is_correct"] is None and meta["mastery_delta"] == 0
    assert meta["concepts"] == [] and meta["concept_items"] == []
    assert runner.repository.add_message.call_args_list[0].args == ("session-1", "user", "？")
    runner.workflow_owner.schedule_semantic_enrichment.assert_not_called()
