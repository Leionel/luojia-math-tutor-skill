import json

import httpx
import pytest

from app.config import get_settings
from app.llm.completion_protocol import ModelCompletionError
from app.llm.openai_compatible import OpenAICompatibleClient


def frame(content=None, finish=None):
    delta = {"content": content} if content is not None else {}
    return "data: " + json.dumps({"choices": [{"delta": delta, "finish_reason": finish}]}) + "\n\n"


@pytest.mark.asyncio
@pytest.mark.parametrize("body,code", [
    (frame("partial"), "model_stream_incomplete"),
    (frame("partial") + frame(finish="length") + "data: [DONE]\n\n", "model_output_truncated"),
    (frame(finish="content_filter") + "data: [DONE]\n\n", "model_output_filtered"),
    (frame(finish="tool_calls"), "model_tool_call_unsupported"),
    ("data: [DONE]\n\n", "model_empty_output"),
    ("data: not-json\n\n", "model_response_invalid"),
    ('data: {"error":{"message":"private vendor token"}}\n\n', "model_provider_error"),
])
async def test_provider_failures_cannot_complete(body, code):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=body))
    async with httpx.AsyncClient(transport=transport) as http:
        client = OpenAICompatibleClient(get_settings().model_copy(update={"llm_api_key": "offline-fixture"}))
        client.get_http_client = lambda: http
        with pytest.raises(ModelCompletionError) as error:
            _ = [chunk async for chunk in client.stream([{"role": "user", "content": "q"}])]
        assert error.value.code == code
        assert "private vendor token" not in str(error.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("ending", [
    frame(finish="stop"),
    "data: [DONE]\n\n",
    frame(finish="stop") + 'data: {"choices":[],"usage":{"total_tokens":7}}\n\n' + "data: [DONE]\n\n",
])
async def test_explicit_terminal_and_usage_chunks_complete(ending):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=frame("answer") + ending))
    async with httpx.AsyncClient(transport=transport) as http:
        client = OpenAICompatibleClient(get_settings().model_copy(update={"llm_api_key": "offline-fixture"}))
        client.get_http_client = lambda: http
        chunks = [chunk async for chunk in client.stream([{"role": "user", "content": "q"}])]
        assert chunks == [{"type": "content", "content": "answer"}]


@pytest.mark.asyncio
async def test_nonstream_truncation_and_missing_configuration_are_failures():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={
        "choices": [{"message": {"content": "partial"}, "finish_reason": "length"}]}))
    async with httpx.AsyncClient(transport=transport) as http:
        client = OpenAICompatibleClient(get_settings().model_copy(update={"llm_api_key": "offline-fixture"}))
        client.get_http_client = lambda: http
        with pytest.raises(ModelCompletionError, match="长度限制"):
            await client.chat_completion([])
    client = OpenAICompatibleClient(get_settings().model_copy(update={"llm_api_key": None}))
    with pytest.raises(ModelCompletionError) as error:
        _ = [chunk async for chunk in client.stream([])]
    assert error.value.code == "model_not_configured"


@pytest.mark.asyncio
@pytest.mark.parametrize("payload,code", [
    ("not-json", "model_response_invalid"),
    ('{"error":{"message":"private vendor token"}}', "model_provider_error"),
    ('{"choices":[]}', "model_response_invalid"),
    ('{"choices":[{"message":{"content":""},"finish_reason":"stop"}]}', "model_empty_output"),
])
async def test_nonstream_invalid_and_empty_results_use_safe_error_codes(payload, code):
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=payload))
    async with httpx.AsyncClient(transport=transport) as http:
        client = OpenAICompatibleClient(get_settings().model_copy(update={"llm_api_key": "offline-fixture"}))
        client.get_http_client = lambda: http
        with pytest.raises(ModelCompletionError) as error:
            await client.chat_completion([])
        assert error.value.code == code and "private vendor token" not in str(error.value)
