import pytest
from app.config import get_settings
from app.llm.openai_compatible import OpenAICompatibleClient


def test_build_payload_deepseek_effort():
    settings = get_settings()
    client = OpenAICompatibleClient(settings)

    # DeepSeek medium -> high (official default)
    p_med = client.build_request_payload(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "ping"}],
        effort="medium",
        enable_search=False,
    )
    assert p_med["reasoning_effort"] == "high"

    # DeepSeek max -> max
    p_max = client.build_request_payload(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "ping"}],
        effort="max",
        enable_search=False,
    )
    assert p_max["reasoning_effort"] == "max"

    # DeepSeek off -> thinking disabled
    p_off = client.build_request_payload(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "ping"}],
        effort="off",
        enable_search=False,
    )
    assert p_off.get("thinking", {}).get("type") == "disabled"


def test_build_payload_qwen_search_and_effort():
    settings = get_settings()
    client = OpenAICompatibleClient(settings)

    # Qwen with enable_search=True
    p_search = client.build_request_payload(
        model="qwen-plus",
        messages=[{"role": "user", "content": "ping"}],
        effort="medium",
        enable_search=True,
    )
    assert p_search["enable_search"] is True
    assert p_search.get("thinking_budget") == 4096

    # Qwen with effort off
    p_off = client.build_request_payload(
        model="qwen-plus",
        messages=[{"role": "user", "content": "ping"}],
        effort="off",
        enable_search=False,
    )
    assert p_off.get("enable_thinking") is False


def test_build_payload_glm_search_and_effort():
    settings = get_settings()
    client = OpenAICompatibleClient(settings)

    p_glm = client.build_request_payload(
        model="glm-4.7",
        messages=[{"role": "user", "content": "ping"}],
        effort="max",
        enable_search=True,
    )
    # GLM native tools
    assert any(t.get("type") == "web_search" for t in p_glm.get("tools", []))
    assert p_glm.get("reasoning_effort") == "max"
