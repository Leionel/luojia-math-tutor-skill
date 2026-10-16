from unittest.mock import AsyncMock

import pytest

from app.tutor.answer_guard import (AnswerDeliveryError, answer_requested, check_delivery,
                                    check_root_contract, guard_report)
from test_agent_graph import make_config, make_repository, make_state
from app.config import get_settings
from app.tutor.graph import TutorWorkflow


@pytest.mark.parametrize("text,rule", [
    ("", "empty_body"),
    ("[TOOL_RESULT] internal", "internal_protocol"),
    ("我已运行你的代码。", "student_code_execution_claim"),
    ("本轮已经执行了学生的Python代码。", "student_code_execution_claim"),
    ("I have executed your code.", "student_code_execution_claim"),
    ("已成功执行代码，结果如下。", "execution_without_evidence"),
    ("我运行了代码。", "execution_without_evidence"),
    ("全部结论已经通过严格数学验证。", "whole_answer_validation_claim"),
    ("工具执行成功，证明整段结论正确。", "whole_answer_validation_claim"),
])
def test_explicit_unsupported_assertions_are_flagged(text, rule):
    assert rule in check_delivery(text).violations


@pytest.mark.parametrize("text", [
    "没有执行你的代码。", "我没有运行你的代码。", "本轮尚未执行代码。",
    "不能说全部结论已经通过严格数学验证。", "全部结论尚未通过严格数学验证。",
    '例子：“我已运行你的代码。”', '学生写道："已成功执行代码。"',
    "> 我已运行你的代码。\n这只是引用，不是实际执行。",
    "```python\nprint('我已运行你的代码')\n```",
    "`[VERIFY]` 是内部协议的例子。",
    "I have not executed your code.", "这一步的导数核对结果与预期相同。",
])
def test_negation_quotations_and_code_examples_are_not_assertions(text):
    assert check_delivery(text).passed


def test_execution_success_cannot_prove_whole_answer_or_student_program():
    assert check_delivery("已执行代码。", execution_succeeded=True).passed
    assert not check_delivery("全部结论已严格验证。", execution_succeeded=True).passed
    assert not check_delivery("已执行你的程序。", execution_succeeded=True).passed


@pytest.mark.parametrize("text", ["答案：x = 2", "### 参考答案：2", "标准答案是 2", "Answer: 2"])
def test_exercise_explicit_answer_section_requires_request(text):
    assert "exercise_answer_disclosure" in check_delivery(text, exercise=True).violations
    assert check_delivery(text, exercise=True, allow_answer=True).passed
    assert check_delivery(text, exercise=False).passed


@pytest.mark.parametrize("text", ["答案：____", "答案：待填写", "请独立完成这道练习。", "暂不提供标准答案是 2 的说法。"])
def test_exercise_placeholders_and_negated_examples_are_allowed(text):
    assert check_delivery(text, exercise=True).passed


def test_explicit_request_respects_negation():
    assert answer_requested("生成题目并附上答案")
    assert not answer_requested("不要给答案，先让我做")
    assert not answer_requested("请不要附上答案")


@pytest.mark.asyncio
async def test_guard_repairs_once_without_executing_tool_and_before_delivery(monkeypatch):
    workflow = TutorWorkflow(get_settings(), make_repository())
    responses = iter(["我已运行你的代码。", "没有执行你的完整程序，这是阅读建议。"])
    async def stream(*args, **kwargs):
        yield {"type": "content", "content": next(responses)}
    workflow.llm.stream = stream
    tool = AsyncMock(side_effect=AssertionError("repair must not execute"))
    monkeypatch.setattr("app.agents.code_executor.execute_python_result", tool)
    state = make_state("什么是导数？")
    config = make_config()
    result = await workflow.workflow.ainvoke(state, config=config)
    assert result["answer_guard"]["status"] == "repaired"
    assert result["answer_guard"]["repair_count"] == 1
    assert result["metrics"]["llm_call_count"] == 2
    assert "我已运行你的代码" not in result["final_output"]
    assert len(config["configurable"]["on_token"].await_args_list) == 1
    tool.assert_not_awaited()


@pytest.mark.asyncio
async def test_second_violation_withholds_without_third_call_or_candidate_delivery():
    workflow = TutorWorkflow(get_settings(), make_repository())
    calls = []
    async def stream(*args, **kwargs):
        calls.append(1)
        yield {"type": "content", "content": "我已运行你的代码。"}
    workflow.llm.stream = stream
    config = make_config()
    with pytest.raises(AnswerDeliveryError) as error:
        await workflow.workflow.ainvoke(make_state("什么是导数？"), config=config)
    assert error.value.report["status"] == "withheld" and len(calls) == 2
    config["configurable"]["on_token"].assert_not_awaited()


@pytest.mark.asyncio
async def test_guard_exception_fails_closed(monkeypatch):
    workflow = TutorWorkflow(get_settings(), make_repository())
    def broken(*args, **kwargs):
        raise RuntimeError("private fixture payload")
    monkeypatch.setattr("app.tutor.graph.check_delivery", broken)
    with pytest.raises(AnswerDeliveryError) as error:
        await workflow._guard_answer("public", [], make_state("什么是导数？"), False, {})
    assert error.value.code == "answer_guard_unavailable"
    assert "private" not in str(error.value)


def test_root_contract_checks_only_receipt_and_rejects_inconsistent_complete_flag():
    report = {"complete": True, "status": "supported", "summary": "controlled feedback"}
    original = report.copy()
    assert check_root_contract(report, "controlled feedback")["scope"] == "delivery_rules_only"
    assert report == original
    with pytest.raises(AnswerDeliveryError):
        check_root_contract({**report, "status": "contradicted"}, "controlled feedback")


def test_guard_metadata_does_not_assert_mathematical_correctness():
    from app.tutor.orchestrator import TutorOrchestrator
    state = make_state("什么是导数？")
    state["answer_guard"] = guard_report("passed")
    meta = TutorOrchestrator._build_learning_meta(state)
    assert not meta["verified"] and meta["is_correct"] is None


@pytest.mark.asyncio
async def test_repair_tool_request_is_withheld_without_executing(monkeypatch):
    workflow = TutorWorkflow(get_settings(),make_repository())
    async def stream(*args,**kwargs):
        yield {"type":"content","content":"[VERIFY]\n```python\nprint(2)\n```\n[OUTPUT]\n提示"}
    workflow.llm.stream=stream
    tool=AsyncMock()
    monkeypatch.setattr("app.agents.code_executor.execute_python_result",tool)
    with pytest.raises(AnswerDeliveryError):
        await workflow._guard_answer("我已运行你的代码。",[],make_state("什么是导数"),False,{})
    tool.assert_not_awaited()


@pytest.mark.asyncio
async def test_disabled_guard_is_unavailable_and_empty_completion_gate_survives():
    from app.llm.completion_protocol import ModelCompletionError
    workflow=TutorWorkflow(get_settings().model_copy(update={"answer_guard_enabled":False}),make_repository())
    _, report=await workflow._guard_answer("文字",[],make_state("什么是导数"),False,{})
    assert not report["enabled"] and report["status"]=="unavailable"
    async def empty(*args,**kwargs):
        yield {"type":"content","content":""}
    workflow.llm.stream=empty
    with pytest.raises(ModelCompletionError):
        await workflow.workflow.ainvoke(make_state("什么是导数"),config=make_config())


@pytest.mark.asyncio
async def test_retired_python_request_cannot_become_execution_evidence(monkeypatch):
    workflow=TutorWorkflow(get_settings(),make_repository())
    async def stream(*args,**kwargs):
        yield {"type":"content","content":"[VERIFY]\n```python\npass\n```\n[OUTPUT]\n没有完成验算。"}
    workflow.llm.stream=stream
    forbidden=AsyncMock(side_effect=AssertionError("generated code is retired"))
    monkeypatch.setattr("app.agents.code_executor.execute_python_result", forbidden)
    result=await workflow.workflow.ainvoke(make_state("什么是导数？"),config=make_config())
    assert result["answer_guard"]["status"]=="passed"
    assert result["metrics"]["llm_call_count"]==1
    assert result["metrics"]["sandbox_successful_calls"]==0
    assert "没有执行模型生成的代码" in result["final_output"]
    forbidden.assert_not_awaited()
