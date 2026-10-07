import asyncio
import time
from dataclasses import asdict, replace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.agents.typed_tools import ToolCall, MathToolResult
from app.config import Settings
from app.math_tools.step_checker import check_step, digest
from app.math_tools.step_runtime import verify_student_step
from app.math_tools.verifier import VerifyResult, parse_math
from app.memory.repository import Repository
from app.tutor.fast_context import FastContextCollector
from app.tutor.graph import TutorWorkflow
from app.tutor.intent_router import Intent
from app.tutor.orchestrator import TutorOrchestrator
from test_agent_graph import make_repository, make_state, make_config, install_fake_stream


@pytest.mark.parametrize("message,correct,eligible", [
    ("我算 d(x^2)/dx=2x，对吗？", True, True),
    ("我算 d(x²)/dx=x，对吗？", False, True),
    ("这一步 2x=x+x 对吗", True, True),
    ("x是实数，sqrt(x^2)=|x| 对吗", True, True),
    ("这一步 x/x=1 对吗", True, False),
    ("这一步 x/x=1 对所有实数成立，对吗", None, False),
    ("帮我检查求导 x**2", None, False),
    ("帮我检查求导 e^x", None, False),
    ("帮我检查求导 x**(1/2)", None, False),
    ("互斥和独立不是一回事，对吗", None, False),
    ("A、B互斥是不是就独立？", None, False),
    ("lim x->0 (x*sin(1/x))/sin(x) 能用洛必达吗？", None, False),
    ("我算 ∫x^2 dx=x^3/3+C，对吗？", True, True),
    ("已知x=0，这一步 x=0 对吗", None, False),
    ("x>0时，这一步 sqrt(x^2)=x 对吗", None, False),
    ("x∈C，sqrt(x^2)=|x| 对吗", None, False),
    ("x∈R+，这一步 sqrt(x^2)=x 对吗", None, False),
    ("x为正数，sqrt(x^2)=x 对吗", None, False),
    ("已知x是实数，sqrt(x^2)=|x| 对吗", True, True),
])
def test_normal_matrix_and_source_qualification(message, correct, eligible):
    result, mistake = check_step(message)
    assert result.is_correct is correct
    assert result.eligible_learning_evidence is eligible
    assert result.input_hash == digest(message)
    if correct is None or not eligible:
        assert mistake is None
    if "x/x" in message:
        assert "x ≠ 0" in result.summary
    if "洛必达" in message:
        assert result.scope == "indeterminate_form" and result.actual == "0/0"
        assert "不能确认" in result.summary


@pytest.mark.parametrize("source", [
    "__import__('builtins').len('abc')", "(x).__class__", "open('file')",
    "lambda: x", "[x for x in (1,2)]", "x[0]", "x+y", "(x**8)**8", "9" * 100,
])
def test_student_syntax_has_no_python_capability(source):
    with pytest.raises(ValueError):
        parse_math(source)
    result, mistake = check_step(f"这一步 {source}=3 对吗")
    assert result.is_correct is None and not result.eligible_learning_evidence
    assert mistake is None


def test_private_operation_cannot_be_selected_by_a_model():
    with pytest.raises(ValidationError):
        ToolCall(call_id="malicious", name="student_step_check", arguments={"message": "x=x"})


@pytest.mark.asyncio
async def test_fixed_worker_preserves_normal_checks_beyond_retrieval_deadline(monkeypatch):
    repository = make_repository()
    collector = FastContextCollector(repository, timeout_seconds=.01)
    monkeypatch.setattr(collector, "_collect_local_hits", AsyncMock(return_value=(None, 0)))
    context = await collector.collect(make_state("我算 d(x^2)/dx=2x，对吗？"))
    assert context.verifier_result.is_correct is True
    assert context.verifier_result.eligible_learning_evidence
    assert context.metrics["symbolic_verify_ms"] > 10


@pytest.mark.asyncio
async def test_parent_deadline_is_not_reset(monkeypatch):
    repository = make_repository()
    collector = FastContextCollector(repository)
    monkeypatch.setattr(collector, "_collect_local_hits", AsyncMock(return_value=(None, 0)))
    state = make_state("我算 d(x^2)/dx=2x，对吗？")
    state["request_deadline"] = time.perf_counter() - 1
    context = await collector.collect(state)
    assert context.verifier_result.execution_status == "timeout"
    assert context.verifier_result.is_correct is None
    repository.upsert_mastery.assert_not_called()


@pytest.mark.parametrize("kind", ["calculation", "heuristic", "unknown_with_mistake", "wrong_input", "scoped"])
def test_both_learning_sinks_fail_closed(kind):
    message = "我算 d(x^2)/dx=x，对吗？"
    result, _ = check_step(message)
    from app.tutor.misconception import MISTAKES
    if kind == "calculation": result, _ = check_step("帮我检查求导 x^2")
    if kind == "heuristic": result, _ = check_step("互斥和独立不是一回事，对吗")
    if kind == "unknown_with_mistake": result = replace(result, verified=False, is_correct=None)
    if kind == "wrong_input": result = replace(result, input_hash="0" * 64)
    if kind == "scoped": result, _ = check_step("这一步 x/x=1 对吗")
    repository = make_repository()
    collector = FastContextCollector(repository)
    collector._finalize_learning_state(make_state(message), ["导数"], result, MISTAKES["CHAIN_RULE_MISSING_INNER_DERIVATIVE"])
    repository.add_mistake_event.assert_not_called()
    repository.upsert_mastery.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("tamper", ["input", "candidate"])
async def test_worker_response_cannot_rebind_another_input(monkeypatch, tamper):
    from app.math_tools import step_runtime
    message = "这一步 2x=x+x 对吗"
    wrong, _ = check_step("这一步 x=x 对吗" if tamper == "input" else message)
    if tamper == "candidate": wrong.candidate_hash = "0" * 64
    monkeypatch.setattr(step_runtime, "run_fixed_worker", AsyncMock(return_value=MathToolResult(
        "succeeded", data={"verification": asdict(wrong), "mistake_code": None})))
    result, _ = await verify_student_step(message)
    assert result.execution_status == "failed" and result.is_correct is None


@pytest.mark.parametrize("reason", ["cancel", "help_changed"])
@pytest.mark.asyncio
async def test_private_worker_is_reaped_on_cancel_or_help_change(monkeypatch, reason):
    from app.agents import typed_tools
    from app.tutor import help_boundary
    processes = []
    original = typed_tools.subprocess.Popen
    def record(*args, **kwargs):
        proc = original(*args, **kwargs)
        processes.append(proc)
        return proc
    monkeypatch.setattr(typed_tools.subprocess, "Popen", record)
    locked = False
    def help_gate(*args):
        if locked: raise ValueError("assessment started")
    monkeypatch.setattr(help_boundary, "assert_reference_help_allowed", help_gate)
    task = asyncio.create_task(verify_student_step("我算 d(x^2)/dx=2x，对吗？", owner="synthetic"))
    async with asyncio.timeout(5):
        while not processes: await asyncio.sleep(.01)
    if reason == "cancel":
        task.cancel()
        with pytest.raises(asyncio.CancelledError): await task
    else:
        locked = True
        result, _ = await task
        assert result.execution_status == "rejected" and result.is_correct is None
    assert all(process.poll() is not None for process in processes)


@pytest.mark.parametrize("message,should_update", [
    ("我算 d(x^2)/dx=2x，对吗？", True),
    ("帮我检查求导 x**2", False),
    ("互斥和独立不是一回事，对吗", False),
])
@pytest.mark.asyncio
async def test_real_graph_sqlite_and_saved_metadata(message, should_update, tmp_path, monkeypatch):
    settings = Settings(database_url=f"sqlite:///{tmp_path/'student.db'}")
    repository = Repository(settings)
    session = repository.create_session("s50-student", "calculus")
    repository.add_message(session["session_id"], "assistant", "上一轮讨论导数。", learning_meta={"concepts": ["导数"]})
    repository.upsert_mastery = MagicMock(wraps=repository.upsert_mastery)
    repository.add_mistake_event = MagicMock(wraps=repository.add_mistake_event)
    workflow = TutorWorkflow(settings, repository)
    monkeypatch.setattr(workflow.context_collector, "_collect_local_hits", AsyncMock(return_value=(None, 0)))
    install_fake_stream(workflow, "[OUTPUT] 这里讨论的是你提交的这一行。自动检查只覆盖本轮说明的范围，参考计算不是你的独立作答。你使用了什么条件？")
    workflow.llm.chat_completion = AsyncMock(return_value='{"verified":false,"is_correct":null,"error_step":null,"reason":"范围不足","summary":"本轮仅作推理审查意见"}')
    state = make_state(message)
    state.update(user_id="s50-student", session_id=session["session_id"])
    final = await workflow.workflow.ainvoke(state, config=make_config(session["session_id"]))
    if "帮我检查求导" in message:
        workflow.llm.chat_completion.assert_not_awaited()
        assert "未能完成符号验算" not in final["final_output"]
    meta = TutorOrchestrator._build_learning_meta(final)
    repository.add_message(session["session_id"], "assistant", final["final_output"], learning_meta=meta)
    restored = repository.list_messages(session["session_id"])[-1]["learning_meta"]
    assert restored["step_check"] == meta["step_check"]
    assert restored["step_check"]["input_hash"] == digest(message)
    assert restored["step_check"]["eligible_learning_evidence"] is should_update
    assert repository.upsert_mastery.called is should_update
    repository.add_mistake_event.assert_not_called()
    if not should_update:
        assert all(not item["assessed"] for item in restored["concept_items"])
    # Original historical text is preserved in storage, only the prompt gets a provenance prefix.
    assert repository.list_messages(session["session_id"])[0]["content"] == "上一轮讨论导数。"


@pytest.mark.parametrize("message", ["我算 d(x²)/dx=2x，对吗？", "帮我检查求导 x**2"])
def test_authenticated_sse_persists_the_same_scoped_result(message, tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api import routes_tutor
    from app.auth import Principal, get_principal
    from test_orchestrator import parse_event
    settings = Settings(database_url=f"sqlite:///{tmp_path/'stream.db'}")
    repository = Repository(settings)
    session = repository.create_session("s50-http", "calculus")
    orchestrator = TutorOrchestrator(settings, repository)
    monkeypatch.setattr(orchestrator.workflow_owner.context_collector, "_collect_local_hits", AsyncMock(return_value=(None, 0)))
    install_fake_stream(orchestrator.workflow_owner, "[OUTPUT] 本轮只核对你提交的一行，检查范围已经说明。参考计算不是独立作答；你使用了什么条件？")
    orchestrator.workflow_owner.llm.chat_completion = AsyncMock(return_value='{"verified":false,"is_correct":null,"error_step":null,"reason":"范围不足","summary":"推理审查意见"}')
    app = FastAPI()
    app.include_router(routes_tutor.router)
    app.dependency_overrides[routes_tutor.get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[routes_tutor.get_app_settings] = lambda: settings
    app.dependency_overrides[get_principal] = lambda: Principal("s50-http", True, "student")
    response = TestClient(app).post("/api/tutor/stream", json={"user_id":"s50-http", "session_id":session["session_id"], "message":message,"subject":"calculus"})
    assert response.status_code == 200
    events = [parse_event(block) for block in response.text.split("\n\n") if block.strip()]
    scoped = [data["step_check"] for name, data in events if name == "meta" and data.get("step_check")]
    saved = repository.list_messages(session["session_id"])[-1]
    assert saved["role"] == "assistant", events
    assert scoped and saved["learning_meta"]["step_check"] == scoped[-1]
    assert saved["learning_meta"]["step_check"]["input_hash"] == digest(message)
    if "帮我" in message:
        assert not saved["learning_meta"]["step_check"]["eligible_learning_evidence"]
        assert repository.get_mastery("s50-http", "导数") is None
