from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.tool_result import ToolExecutionResult
from app.config import get_settings
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.tutor.fast_path import route_fast_path
from app.tutor.graph import (
    TutorWorkflow,
    route_after_context,
)
from app.tutor.policy_router import PedagogicalAction, PolicyDecision
from app.tutor.intent_router import Intent


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
            "on_progress": AsyncMock(),
        }
    }


def install_fake_stream(workflow: TutorWorkflow, text: str) -> None:
    async def fake_stream(messages, api_key=None, model=None, **kwargs):
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


def test_complex_proof_routes_through_proof_tutor():
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
    # The production 0.35s budget is intentionally tight; a cold first call
    # can spend it all on imports before the symbolic check (a few ms) lands.
    # This test verifies routing, not the latency budget, so lift it.
    workflow.context_collector.timeout_seconds = 10.0
    workflow.llm.chat_completion = AsyncMock()

    # First response skips verification; after the forced re-prompt the model
    # complies with a sandbox check and produces the visible answer.
    responses = iter([
        "[OUTPUT] 这一步可以通过对结果求导来核对。",
        "[VERIFY]\n```python\nfrom sympy import diff, symbols\nx = symbols('x')\nprint(diff(x**2 + 0, x))\n```\n[OUTPUT] 我们对 x^2 + C 求导来核对这一步。",
        "[OUTPUT] 求导结果为 2x，这一步核对无误。",
    ])
    seen_prompts: list[list[dict]] = []

    async def scripted_stream(messages, api_key=None, model=None, **kwargs):
        seen_prompts.append(list(messages))
        yield {"type": "content", "content": next(responses)}

    workflow.llm.stream = scripted_stream
    state = make_state("我算 ∫2x dx = x^2 + C，对吗？")

    final_state = await workflow.workflow.ainvoke(
        state,
        config=make_config(state["session_id"]),
    )

    assert final_state["verifier_result"].verified is True
    # The verifier LLM node is skipped, but the hard gate forces the teacher
    # through: (0) unverified draft, (1) forced [VERIFY] round, (2) final
    # answer after the sandbox result — three streamed model calls in total.
    assert final_state["metrics"]["llm_call_count"] == 3
    assert final_state["metrics"]["verification_enforced"] == "enforced"
    assert final_state["metrics"]["sandbox_tool_calls"] >= 1
    flattened = " ".join(str(m.get("content", "")) for m in seen_prompts[1])
    assert "[系统强制要求]" in flattened
    workflow.llm.chat_completion.assert_not_awaited()


@pytest.mark.asyncio
async def test_complex_proof_is_reviewed_before_tutoring():
    workflow = TutorWorkflow(get_settings(), make_repository())
    workflow.llm.chat_completion = AsyncMock(return_value='{"verified": true, "is_correct": null, "error_step": null, "reason": "需给出学生步骤", "summary": "审查题目条件"}')
    install_fake_stream(workflow, "先明确定理中的条件分别起什么作用。")
    state = make_state("证明拉格朗日中值定理")

    final_state = await workflow.workflow.ainvoke(
        state,
        config=make_config(state["session_id"]),
    )

    assert final_state["metrics"]["llm_call_count"] == 2
    assert final_state["metrics"]["route"] == "proof_tutor"


@pytest.mark.asyncio
async def test_policy_fallback_does_not_duplicate_user_prompt():
    workflow = TutorWorkflow(get_settings(), make_repository())
    workflow.policy_router.decide_route = AsyncMock(
        return_value=PolicyDecision(Intent.CONCEPT, PedagogicalAction.EXPLAIN, 0.9, False)
    )
    captured_prompt = []

    async def fake_stream(messages, api_key=None, model=None, **kwargs):
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


@pytest.mark.asyncio
async def test_uncertain_policy_stops_before_learning_writes_or_generation():
    repository = make_repository()
    workflow = TutorWorkflow(get_settings(), repository)
    workflow.policy_router.decide_route = AsyncMock(return_value=PolicyDecision(
        Intent.SOLVE_STEP_BY_STEP, PedagogicalAction.HINT, 0.2, True))
    workflow.context_collector.collect = AsyncMock(side_effect=AssertionError("must not collect"))
    workflow.llm.stream = MagicMock(side_effect=AssertionError("must not generate"))
    state = make_state("？")
    final = await workflow.workflow.ainvoke(state, config=make_config())
    assert final["awaiting_intent_clarification"]
    assert final["metrics"]["route"] == "intent_clarification"
    assert final["mastery_delta"] == 0
    workflow.context_collector.collect.assert_not_awaited()
    repository.add_attempt.assert_not_called()
    repository.upsert_mastery.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("intent,action,verification", [
    (Intent.CHECK_STUDENT_STEP, PedagogicalAction.ASK_QUESTION, "symbolic"),
    (Intent.PROOF_HINT, PedagogicalAction.PROVIDE_HINT, "llm"),
])
async def test_resolved_policy_recomputes_verification_before_context(intent, action, verification):
    repository = make_repository()
    repository.list_messages.return_value = [{"role": "user", "content": "请检查下一步"}]
    workflow = TutorWorkflow(get_settings(), repository)
    workflow.policy_router.decide_route = AsyncMock(return_value=PolicyDecision(intent, action, 0.9, False))
    workflow.context_collector.collect = AsyncMock(side_effect=RuntimeError("context reached"))
    state = make_state("x = 2")
    state.update(requires_policy_fallback=True, verification_mode="none")
    with pytest.raises(RuntimeError, match="context reached"):
        await workflow.workflow.ainvoke(state, config=make_config())
    resolved = workflow.context_collector.collect.call_args.args[0]
    assert resolved["intent"] is intent and resolved["verification_mode"] == verification
    assert not resolved["requires_policy_fallback"]
    assert workflow.policy_router.decide_route.call_args.kwargs["history"] == repository.list_messages.return_value


@pytest.mark.asyncio
async def test_protocol_only_draft_is_not_delivered_as_an_answer():
    from app.llm.completion_protocol import ModelCompletionError
    workflow = TutorWorkflow(get_settings(), make_repository())
    install_fake_stream(workflow, "[PLAN] 我会继续考虑。")
    config = make_config()
    with pytest.raises(ModelCompletionError) as error:
        await workflow.workflow.ainvoke(make_state("什么是导数？"), config=config)
    assert error.value.code == "model_empty_output"
    config["configurable"]["on_token"].assert_not_awaited()


@pytest.mark.asyncio
async def test_model_reasoning_is_not_forwarded_or_persisted():
    workflow = TutorWorkflow(get_settings(), make_repository())

    async def fake_stream(messages, api_key=None, model=None, **kwargs):
        yield {"type": "reasoning", "content": "private chain of thought"}
        yield {"type": "content", "content": "公开回答"}

    workflow.llm.stream = fake_stream
    state = make_state("什么是导数？")
    config = make_config(state["session_id"])

    final_state = await workflow.workflow.ainvoke(state, config=config)

    assert final_state["final_output"] == "公开回答"
    assert final_state["thinking_chain"] == ""
    thinking_events = [
        call.args[0]
        for call in config["configurable"]["on_thinking"].await_args_list
    ]
    assert all("private chain of thought" not in event for event in thinking_events)


@pytest.mark.asyncio
async def test_teacher_executes_requested_verification_before_showing_output(monkeypatch):
    workflow = TutorWorkflow(get_settings(), make_repository())
    responses = iter([
        "[VERIFY]\n```python\nprint(2 + 2)\n```\n[OUTPUT]\n尚未核对",
        "[OUTPUT]\n已核对，结果是 4。",
    ])

    async def fake_stream(messages, api_key=None, model=None, **kwargs):
        yield {"type": "content", "content": next(responses)}

    execute = AsyncMock(return_value=ToolExecutionResult("succeeded", stdout="4", exit_code=0))
    monkeypatch.setattr("app.tutor.graph.execute_python_result", execute)
    workflow.llm.stream = fake_stream
    state = make_state("请核对 2+2")
    state["messages"] = [{"role": "system", "content": "skill"}, {"role": "user", "content": state["message"]}]

    result = await workflow.teacher_node(state, make_config())

    execute.assert_awaited_once_with("print(2 + 2)", timeout=workflow.settings.tool_timeout_seconds)
    assert result["final_output"].endswith("已核对，结果是 4。")
    assert "不等于下文全部结论已经得到数学验证" in result["final_output"]
    assert result["metrics"]["tool_validation_scope"] == "execution_only"
    assert result["metrics"]["sandbox_tool_calls"] == 1
    assert "尚未核对" not in result["final_output"]


@pytest.mark.asyncio
async def test_vision_parse_enriches_the_turn_and_emits_confirmation():
    workflow = TutorWorkflow(get_settings(), make_repository())
    workflow.vision_parser.parse_images = AsyncMock(return_value={
        "problem_text": "求 x^2 的导数",
        "latex": ["x^2"],
        "confidence": 0.98,
        "needs_confirmation": True,
    })
    state = make_state("请看图")
    state["image_urls"] = ["data:image/png;base64,aA=="]
    config = make_config()

    result = await workflow.vision_parse_node(state, config)

    assert "求 x^2 的导数" in result["message"]
    events = [call.args[0] for call in config["configurable"]["on_thinking"].await_args_list]
    assert any("event: vision_confirmation" in event for event in events)
