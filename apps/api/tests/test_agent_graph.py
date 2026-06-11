from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import get_settings
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.tutor.fast_path import route_fast_path
from app.tutor.graph import (
    TutorWorkflow,
    route_after_context,
)
from app.tutor.policy_router import PedagogicalAction


def make_repository() -> MagicMock:
    repository = MagicMock(spec=Repository)
    repository.list_messages.return_value = []
    repository.list_sessions.return_value = []
    repository.get_mastery.return_value = None
    repository.get_consecutive_errors.return_value = 0
    repository.add_message.return_value = "message-1"
    return repository


def make_state(message: str, mode: str = "socratic") -> dict:
    route = route_fast_path(message, mode=mode, subject="calculus")
    return {
        "message": message,
        "session_id": f"session-{abs(hash(message))}",
        "user_id": "user-1",
        "subject": "calculus",
        "mode": mode,
        "user_api_key": None,
        "model": None,
        "requested_hint": False,
        "image_urls": None,
        "intent": route.intent,
        "detected_subject": route.subject,
        "pedagogical_action": route.pedagogical_action,
        "learning_objective": route.learning_objective,
        "verification_mode": route.verification_mode.value,
        "confidence": route.confidence,
        "requires_policy_fallback": route.requires_policy_fallback,
        "hits": [],
        "document_chunks": [],
        "verifier_result": VerifyResult(
            False,
            None,
            "本轮未触发自动验证。",
        ),
        "verification_result": {},
        "mistake": None,
        "concepts": [],
        "mastery_score": 0.5,
        "mastery_delta": 0.0,
        "mastery_label_str": "一般",
        "hint_level": 0,
        "messages": [],
        "thinking_steps": [],
        "final_output": "",
        "thinking_chain": "",
        "metrics": {
            "llm_call_count": 0,
            "route": "",
        },
    }


def make_config(session_id: str = "session-1") -> dict:
    return {
        "configurable": {
            "thread_id": session_id,
            "on_token": AsyncMock(),
            "on_thinking": AsyncMock(),
        }
    }


def install_fake_stream(workflow: TutorWorkflow, text: str) -> None:
    async def fake_stream(messages, api_key=None, model=None):
        yield {"type": "content", "content": text}

    workflow.llm.stream = fake_stream


@pytest.mark.asyncio
async def test_tutor_workflow_compiles():
    workflow = TutorWorkflow(get_settings(), make_repository())

    assert workflow.workflow is not None


@pytest.mark.asyncio
async def test_normal_context_uses_local_planner_and_policy():
    workflow = TutorWorkflow(get_settings(), make_repository())
    workflow.llm.chat_completion = AsyncMock(
        side_effect=AssertionError("fast context must not call an LLM")
    )
    state = make_state("什么是导数？")

    result = await workflow.fast_context_node(state, config=make_config())

    assert result["pedagogical_action"] == "explain"
    assert result["learning_objective"]
    workflow.llm.chat_completion.assert_not_awaited()


def test_symbolic_success_routes_directly_to_teacher():
    state = make_state("我算 ∫2x dx = x^2 + C，对吗？")
    state["verifier_result"] = VerifyResult(True, True, "验证通过")

    assert route_after_context(state) == "teacher"


def test_complex_proof_routes_through_verifier():
    state = make_state("证明拉格朗日中值定理")

    assert route_after_context(state) == "verifier"


@pytest.mark.asyncio
async def test_ordinary_request_uses_one_generation_call():
    workflow = TutorWorkflow(get_settings(), make_repository())
    workflow.llm.chat_completion = AsyncMock(
        side_effect=AssertionError("ordinary route must skip internal LLMs")
    )
    install_fake_stream(workflow, "先看瞬时变化率的含义。")
    state = make_state("什么是导数？")

    final_state = await workflow.workflow.ainvoke(
        state,
        config=make_config(state["session_id"]),
    )

    assert final_state["metrics"]["llm_call_count"] == 1
    assert final_state["metrics"]["route"] == "teacher"
    assert final_state["final_output"] == "先看瞬时变化率的含义。"
    workflow.llm.chat_completion.assert_not_awaited()


@pytest.mark.asyncio
async def test_symbolic_success_skips_verifier_llm():
    workflow = TutorWorkflow(get_settings(), make_repository())
    workflow.llm.chat_completion = AsyncMock()
    install_fake_stream(workflow, "这一步可以通过对结果求导来核对。")
    state = make_state("我算 ∫2x dx = x^2 + C，对吗？")

    final_state = await workflow.workflow.ainvoke(
        state,
        config=make_config(state["session_id"]),
    )

    assert final_state["verifier_result"].verified is True
    assert final_state["metrics"]["llm_call_count"] == 1
    workflow.llm.chat_completion.assert_not_awaited()


@pytest.mark.asyncio
async def test_complex_proof_uses_verifier_then_teacher():
    workflow = TutorWorkflow(get_settings(), make_repository())
    workflow.llm.chat_completion = AsyncMock(
        return_value='{"verified": true, "summary": "论证结构可用"}'
    )
    install_fake_stream(workflow, "先明确定理中的条件分别起什么作用。")
    state = make_state("证明拉格朗日中值定理")

    final_state = await workflow.workflow.ainvoke(
        state,
        config=make_config(state["session_id"]),
    )

    assert final_state["metrics"]["llm_call_count"] == 2
    assert final_state["metrics"]["route"] == "verifier_teacher"
    workflow.llm.chat_completion.assert_awaited_once()


@pytest.mark.asyncio
async def test_policy_fallback_does_not_duplicate_user_prompt():
    workflow = TutorWorkflow(get_settings(), make_repository())
    workflow.policy_router.decide_action = AsyncMock(
        return_value=PedagogicalAction.EXPLAIN
    )
    captured_prompt = []

    async def fake_stream(messages, api_key=None, model=None):
        captured_prompt.extend(messages)
        yield {"type": "content", "content": "请先补充题目条件。"}

    workflow.llm.stream = fake_stream
    state = make_state("？")

    final_state = await workflow.workflow.ainvoke(
        state,
        config=make_config(state["session_id"]),
    )

    repeated = [
        item
        for item in captured_prompt
        if item["role"] == "user" and item["content"] == "？"
    ]
    assert len(repeated) == 1
    assert final_state["metrics"]["llm_call_count"] == 2
