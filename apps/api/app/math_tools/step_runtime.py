"""Private fixed-worker operation; never advertised as a model tool."""
from dataclasses import dataclass
import asyncio
import re
import time

from app.agents.typed_tools import run_fixed_worker
from app.math_tools.step_checker import StepCheckRequest, digest, candidate_binding
from app.math_tools.verifier import VerifyResult, CHECKER_VERSION
from app.tutor.misconception import MISTAKES


@dataclass(frozen=True)
class _StepCall:
    name: str = "student_step_check"


async def verify_student_step(message: str, timeout=5, owner=None):
    started = time.perf_counter()
    def unknown(reason, status="failed"):
        description = {"tool_input_budget": "输入超出本步核验预算", "tool_timeout": "核验超时",
                       "tool_parameters_invalid": "输入语法或范围不受支持", "tool_worker_failed": "本步检查未完成",
                       "tool_output_budget": "核验结果超出预算", "tool_empty_result": "未返回有效核验结果"}.get(reason, reason)
        return VerifyResult(False, None, f"本步核验未确定（{description}），不会判定学生错误。",
                            input_hash=digest(message), execution_status=status, unknown_reason=reason), None
    try:
        request = StepCheckRequest(version=CHECKER_VERSION, message=message)
    except ValueError:
        return unknown("输入超出核验预算", "rejected")
    async def check_help():
        if owner:
            from app.tutor.help_boundary import assert_reference_help_allowed
            await asyncio.to_thread(assert_reference_help_allowed, owner)
    async def watch_help():
        while True:
            await asyncio.sleep(.1)
            await check_help()
    worker = monitor = None
    try:
        await check_help()
        remaining = min(timeout, 5) - (time.perf_counter() - started)
        if remaining <= 0:
            return unknown("核验时间预算已耗尽", "timeout")
        worker = asyncio.create_task(run_fixed_worker(_StepCall(), request.model_dump(), timeout=remaining))
        if owner:
            monitor = asyncio.create_task(watch_help())
            done, _ = await asyncio.wait([worker, monitor], return_when=asyncio.FIRST_COMPLETED)
            if monitor in done:
                await monitor  # Boundary failure cancels/reaps the owned worker in finally.
        result = await worker
        await check_help()
    except ValueError:
        return unknown("当前独立检验禁止新增参考帮助", "rejected")
    finally:
        owned = [task for task in (worker, monitor) if task is not None]
        for task in owned:
            if not task.done(): task.cancel()
        if owned: await asyncio.gather(*owned, return_exceptions=True)
    if result.status != "succeeded":
        return unknown(result.error_code or result.status, result.status)
    try:
        data = result.data
        if set(data) != {"verification", "mistake_code"}:
            raise ValueError("response_fields")
        payload = data["verification"]
        verdict = VerifyResult(**payload)
        if (verdict.origin not in {"none", "student_claim", "system_calculation", "classification", "heuristic"}
                or verdict.execution_status not in {"not_requested", "succeeded", "rejected", "timeout", "failed"}
                or verdict.scope not in {"none", "expression_equivalence", "derivative", "integral_candidate", "determinant_2x2", "indeterminate_form"}
                or not isinstance(verdict.assumptions, list) or len(verdict.assumptions) > 32
                or any(not isinstance(item, str) or len(item) > 2048 for item in verdict.assumptions)
                or any(not isinstance(getattr(verdict, field), str) or len(getattr(verdict, field)) > 8192
                       for field in ("summary", "details", "unknown_reason"))):
            raise ValueError("response_scope")
        if verdict.version != CHECKER_VERSION or verdict.input_hash != digest(message):
            raise ValueError("response_binding")
        if (type(verdict.verified) is not bool or type(verdict.eligible_learning_evidence) is not bool
                or type(verdict.scope_complete) is not bool
                or verdict.is_correct is not None and type(verdict.is_correct) is not bool):
            raise ValueError("response_types")
        if verdict.candidate_hash is not None and not re.fullmatch(r"[a-f0-9]{64}", verdict.candidate_hash):
            raise ValueError("candidate_binding")
        if verdict.origin == "student_claim":
            scope, candidate = candidate_binding(message)
            if candidate is None or verdict.scope != scope or verdict.candidate_hash != digest(candidate):
                raise ValueError("candidate_binding")
        if verdict.eligible_learning_evidence and not (verdict.candidate_hash and verdict.origin == "student_claim"
                and verdict.execution_status == "succeeded" and verdict.scope_complete and verdict.verified and verdict.is_correct is not None):
            raise ValueError("response_eligibility")
        code = data["mistake_code"]
        if code is not None and code not in MISTAKES:
            raise ValueError("mistake_code")
        mistake = MISTAKES.get(code) if verdict.eligible_learning_evidence and verdict.is_correct is False else None
        return verdict, mistake
    except (TypeError, ValueError, KeyError):
        return unknown("检查结果格式或来源未能核对")
