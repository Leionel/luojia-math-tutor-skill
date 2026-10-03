"""Fixed, bounded math calls. No source code, plugins, or learning-grade writes."""
import ast
import asyncio
import hashlib
import json
import math
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from app.math_tools.numerical_lab import NumericalTask

MAX_INPUT = 8192
MAX_OUTPUT = 65536
TOOL_VERSION = "v1"


class DifferentiateArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal["v1"] = "v1"
    expression: str = Field(min_length=1, max_length=512)


class NumericalArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: Literal["v1"] = "v1"
    task: NumericalTask


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    call_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    name: Literal["numerical_run", "math_differentiate"]
    arguments: dict


SPECS = {
    "numerical_run": NumericalArgs,
    "math_differentiate": DifferentiateArgs,
}


def wire_tools():
    return [{"type": "function", "function": {"name": name,
             "description": ("只读线性方程组或积分参考计算，不保存实验，不评价学生。" if name == "numerical_run" else
                             "仅对单变量x表达式求导；说明真实定义域，不证明整个回答。"),
             "parameters": model.model_json_schema()}} for name, model in SPECS.items()]


def expression_tree(expression):
    tree = ast.parse(expression.replace("^", "**"), mode="eval")
    if len(list(ast.walk(tree))) > 64:
        raise ValueError("expression_budget")
    def check(node, depth=0):
        if depth > 12:
            raise ValueError("expression_budget")
        if isinstance(node, ast.Expression):
            check(node.body, depth+1)
        elif isinstance(node, ast.Name) and node.id in {"x", "pi", "e"}:
            pass
        elif isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            segment = ast.get_source_segment(expression.replace("^", "**"), node) or ""
            if len(segment) > 32 or not math.isfinite(node.value) or abs(node.value) > 1e12:
                raise ValueError("expression_budget")
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            check(node.operand, depth+1)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            if isinstance(node.op, ast.Pow):
                exponent = node.right
                sign = 1
                if isinstance(exponent, ast.UnaryOp) and isinstance(exponent.op, (ast.USub, ast.UAdd)):
                    sign = -1 if isinstance(exponent.op, ast.USub) else 1
                    exponent = exponent.operand
                if not isinstance(exponent, ast.Constant) or type(exponent.value) is not int or not -8 <= sign*exponent.value <= 8:
                    raise ValueError("expression_budget")
            check(node.left, depth+1); check(node.right, depth+1)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"sin", "cos", "tan", "exp", "log", "sqrt"} and len(node.args) == 1 and not node.keywords:
            check(node.args[0], depth+1)
        else:
            raise ValueError("expression_rejected")
    check(tree)
    return tree


def validate_call(call):
    encoded = json.dumps(call.model_dump(), ensure_ascii=False, allow_nan=False).encode()
    if len(encoded) > MAX_INPUT:
        raise ValueError("tool_input_budget")
    args = SPECS[call.name].model_validate(call.arguments, strict=True)
    if call.name == "math_differentiate":
        expression_tree(args.expression)
    # Reparse numerical fields strictly, including nested integer/float fields.
    elif TypeAdapter(NumericalTask).validate_python(args.task.model_dump(), strict=True) != args.task:
        raise ValueError("tool_parameters_invalid")
    return args.model_dump()


@dataclass(frozen=True)
class MathToolResult:
    status: str
    error_code: str | None = None
    data: dict | None = None
    duration_ms: float = 0

    def public(self, call):
        return {"version": TOOL_VERSION, "call_id": call.call_id, "tool": call.name,
                "status": self.status, "error_code": self.error_code,
                "duration_ms": self.duration_ms, "data": self.data,
                "execution_succeeded": self.status == "succeeded", "has_output": bool(self.data),
                "evidence_kind": "reference_help", "validation_scope": "tool_result_only"}


async def run_fixed_worker(call, arguments, timeout=10):
    """Own and reap the actual fixed child, including cancellation and byte limits."""
    started = time.perf_counter()
    packet = json.dumps({"name": call.name, "arguments": arguments}, allow_nan=False).encode()
    if len(packet) > MAX_INPUT:
        return MathToolResult("rejected", "tool_input_budget")
    proc = None
    threads = []
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()
    lock = threading.Lock()
    def collect(pipe, index):
        try:
            while chunk := pipe.read(4096):
                with lock:
                    remaining = MAX_OUTPUT - sum(map(len, buffers))
                    buffers[index].extend(chunk[:max(0, remaining)])
                    if len(chunk) > remaining:
                        overflow.set()
                        if proc.poll() is None:
                            proc.kill()
                        break
        finally:
            pipe.close()
    try:
        env = {name: os.environ[name] for name in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "APPDATA", "USERPROFILE") if name in os.environ}
        env["LUOJIA_NO_DOTENV"] = "1"
        proc = subprocess.Popen([sys.executable, "-I", "-u", str(Path(__file__).with_name("math_worker.py"))],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                bufsize=0, env=env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        for index, pipe in enumerate((proc.stdout, proc.stderr)):
            thread = threading.Thread(target=collect, args=(pipe, index), daemon=True)
            threads.append(thread); thread.start()
        proc.stdin.write(packet); proc.stdin.close()
        remaining = max(0.001, min(timeout, 10) - (time.perf_counter()-started))
        await asyncio.wait_for(asyncio.to_thread(proc.wait), remaining)
        for thread in threads:
            await asyncio.to_thread(thread.join)
        elapsed = round((time.perf_counter()-started)*1000, 2)
        if overflow.is_set():
            return MathToolResult("failed", "tool_output_budget", duration_ms=elapsed)
        if proc.returncode != 0:
            return MathToolResult("failed", "tool_worker_failed", duration_ms=elapsed)
        data = json.loads(buffers[0])
        if not isinstance(data, dict) or not data:
            return MathToolResult("failed", "tool_empty_result", duration_ms=elapsed)
        if data.get("error_code"):
            return MathToolResult("failed", "tool_parameters_invalid", duration_ms=elapsed)
        return MathToolResult("succeeded", data=data, duration_ms=elapsed)
    except asyncio.CancelledError:
        raise
    except asyncio.TimeoutError:
        return MathToolResult("timeout", "tool_timeout", duration_ms=round((time.perf_counter()-started)*1000, 2))
    except (OSError, ValueError, BrokenPipeError):
        return MathToolResult("failed", "tool_worker_failed", duration_ms=round((time.perf_counter()-started)*1000, 2))
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.kill()
            await asyncio.to_thread(proc.wait)
            for thread in threads:
                await asyncio.to_thread(thread.join)
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()


class ToolRuntime:
    def __init__(self, owner, run_id, timeout=10):
        self.owner, self.run_id, self.timeout = owner, run_id, timeout
        self.calls = {}
        self.used = 0

    def policy(self):
        from app.tutor.help_boundary import assert_reference_help_allowed
        if not self.owner or not self.run_id:
            raise ValueError("tool_policy_rejected")
        assert_reference_help_allowed(self.owner)

    async def execute(self, call, parent_id=None):
        from app.llm.call_observation import span
        metadata = {"parent_id":parent_id} if parent_id else {}
        async with span("tool", tool_name=call.name, tool_call_id=hashlib.sha256(call.call_id.encode()).hexdigest()[:32], **metadata) as event:
            result = await self._execute(call)
            event.update(status="succeeded" if result["status"]=="succeeded" else "degraded", error_code=result["error_code"])
            return result

    async def _execute(self, call):
        self.used += 1
        try:
            self.policy()
        except ValueError:
            return MathToolResult("rejected", "tool_policy_rejected").public(call)
        if self.used > 2:
            return MathToolResult("rejected", "model_tool_budget").public(call)
        try:
            args = validate_call(call)
            fingerprint = hashlib.sha256(json.dumps([call.name, args], sort_keys=True).encode()).hexdigest()
            old = self.calls.get(call.call_id)
            if old:
                if old[0] != fingerprint:
                    raise ValueError("tool_call_id_conflict")
                return old[1]
        except (ValueError, TypeError, OverflowError, RecursionError, SyntaxError):
            return MathToolResult("rejected", "tool_parameters_invalid").public(call)
        result = (await run_fixed_worker(call, args, self.timeout)).public(call)
        # Do not disclose even a successfully computed result after a probe starts.
        try:
            self.policy()
        except ValueError:
            return MathToolResult("rejected", "tool_policy_rejected").public(call)
        if result["status"] == "succeeded":
            from app.knowledge.course_service import get_course_service
            course = get_course_service("numerical_analysis")
            expression = args.get("expression") or args.get("task", {}).get("expression")
            course.overlay_store.record_process_event(
                f"typed-tool:{self.run_id}:{call.call_id}", self.owner, course.course_id, [],
                event_type="hint_exposed", help_level=3,
                metadata={"origin": "typed_math_tool", "tool": call.name, "run_id": self.run_id,
                          "evidence_kind": "reference_help", **({"function": expression} if expression else {})})
        self.calls[call.call_id] = (fingerprint, result)
        return result
