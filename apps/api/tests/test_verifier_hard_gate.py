import pytest

from app.config import Settings
from app.math_tools.verifier import verify_lhopital_conditions
from app.tutor.graph import TutorWorkflow


# ---------------------------------------------------------------------------
# lhopital: symbolic verdict, never keyword verdicts
# ---------------------------------------------------------------------------


def test_lhopital_text_claims_00_but_limit_is_not_indeterminate():
    result = verify_lhopital_conditions(
        "lim x->0 (x^2+1)/(x+1) 是 0/0 未定式，可以直接用洛必达吗？"
    )
    assert result.verified
    assert result.is_correct is False
    assert "分子极限为 1" in result.summary


def test_lhopital_genuine_00_is_confirmed():
    result = verify_lhopital_conditions("lim x->0 sinx/x 能直接用洛必达吗？")
    assert result.verified
    assert result.is_correct is True
    assert "0/0" in result.summary


def test_lhopital_genuine_infty_over_infty_is_confirmed():
    result = verify_lhopital_conditions(
        "lim x->+\\infty (3x^2+2)/(5x^2+1) 是 ∞/∞ 型未定式"
    )
    assert result.verified
    assert result.is_correct is True
    assert "∞/∞" in result.summary


def test_lhopital_without_parseable_expression_fails_closed():
    result = verify_lhopital_conditions("这题可以用洛必达法则吧？")
    assert not result.verified
    assert result.is_correct is None


# ---------------------------------------------------------------------------
# teacher hard gate: forced verification + observable degradation
# ---------------------------------------------------------------------------


class FakeLLM:
    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.prompts: list[list[dict]] = []

    async def stream(self, prompt, api_key=None, model=None):
        self.prompts.append(prompt)
        if not self.responses:
            raise AssertionError("FakeLLM received more model calls than scripted")
        yield self.responses.pop(0)


def _workflow_with(llm: FakeLLM, tool_max_rounds: int = 2) -> TutorWorkflow:
    workflow = TutorWorkflow.__new__(TutorWorkflow)
    workflow.settings = Settings(tool_max_rounds=tool_max_rounds)
    workflow.llm = llm
    return workflow


def _state(**overrides) -> dict:
    state = {
        "message": "lim x->0 sinx/x 是什么类型？",
        "metrics": {},
    }
    state.update(overrides)
    return state


@pytest.mark.asyncio
async def test_missing_verify_tag_triggers_forced_verification_round():
    llm = FakeLLM([
        "[OUTPUT] 直接给结论，不验算。",
        "[VERIFY]\n```python\nprint(2**8)\n```\n[OUTPUT] 验算后给出结论。",
        "[OUTPUT] 验算后给出结论。",
    ])
    workflow = _workflow_with(llm)

    result = await workflow._stream_generation(
        _state(verification_mode="symbolic"),
        None,
        [{"role": "user", "content": "q"}],
        default_route="teacher",
        require_verification=True,
    )

    assert result["metrics"]["verification_enforced"] == "enforced"
    assert result["metrics"]["sandbox_tool_calls"] == 1
    # The forced instruction reached the model as an extra user turn.
    flattened = " ".join(str(m.get("content", "")) for m in llm.prompts[1])
    assert "[系统强制要求]" in flattened
    assert not result["final_output"].startswith("⚠️")


@pytest.mark.asyncio
async def test_unverifiable_output_degrades_observably():
    llm = FakeLLM([
        "[OUTPUT] 第一次回答。",
        "[OUTPUT] 第二次回答，仍然没有验算。",
    ])
    workflow = _workflow_with(llm, tool_max_rounds=1)

    result = await workflow._stream_generation(
        _state(verification_mode="symbolic"),
        None,
        [{"role": "user", "content": "q"}],
        default_route="teacher",
        require_verification=True,
    )

    assert result["metrics"]["verification_enforced"] == "degraded"
    assert result["final_output"].startswith("⚠️ 本轮未能完成符号验算")


@pytest.mark.asyncio
async def test_upstream_verifier_failure_is_surfaced_to_student():
    llm = FakeLLM(["[OUTPUT] 回答。"])
    workflow = _workflow_with(llm)

    result = await workflow._stream_generation(
        _state(
            verification_result={
                "verified": False,
                "summary": "验证服务暂不可用，不应对当前推导作确定性判断。",
            }
        ),
        None,
        [{"role": "user", "content": "q"}],
        default_route="teacher",
    )

    assert result["final_output"].startswith("❗ 验证服务暂不可用")
    assert result["metrics"]["verification_enforced"] == "not_required"


@pytest.mark.asyncio
async def test_no_verification_required_keeps_output_unchanged():
    llm = FakeLLM(["[OUTPUT] 概念性回答。"])
    workflow = _workflow_with(llm)

    result = await workflow._stream_generation(
        _state(),
        None,
        [{"role": "user", "content": "q"}],
        default_route="teacher",
    )

    assert result["final_output"] == "概念性回答。"
    assert result["metrics"]["verification_enforced"] == "not_required"
