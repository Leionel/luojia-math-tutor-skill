import httpx
import pytest
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
