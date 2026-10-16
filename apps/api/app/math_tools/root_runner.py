"""Bounded reference trajectories, separate from submitted student evidence."""
from pydantic import BaseModel, ConfigDict, Field
from app.math_tools.root_expression import RootExpression, ExpressionError
from app.math_tools.root_finding import RootAttempt, diagnose

RUNNER_VERSION = "root-runner-v1"


class LabRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attempt: RootAttempt
    max_iterations: int = Field(default=20, ge=1, le=100)
    prediction: str = Field(min_length=1, max_length=1000)
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")


def run_reference(request: LabRequest) -> dict:
    a = request.attempt
    if a.iterates or a.brackets or a.update or a.derivative:
        raise ValueError("实验参数不接受提交轨迹、自定义程序或导数；请在练习中核对自己的过程。")
    f = RootExpression(a.function)
    phi = RootExpression(a.phi) if a.phi else None
    if a.method == "fixed_point" and phi is None:
        raise ValueError("不动点实验需要 phi(x)。")
    bounds = a.interval
    if bounds and not bounds[0] < bounds[1]:
        raise ValueError("区间下界须小于上界。")
    if a.method == "bisection":
        if not bounds or f.evaluate(bounds[0]) * f.evaluate(bounds[1]) >= 0:
            raise ValueError("二分实验需要严格变号区间；连续性仍须由诊断核对。")
        x = (bounds[0] + bounds[1]) / 2
    else:
        if a.initial_value is None:
            raise ValueError("请填写初值。")
        x = a.initial_value
    trace, brackets, rows = [], [], []
    stop, reason = "iteration_limit", "达到迭代上限"
    for k in range(request.max_iterations + 1):
        try:
            residual = f.evaluate(x)
            step = abs(x - trace[-1]) if trace else None
            trace.append(x)
            if a.method == "bisection":
                brackets.append(bounds)
            rows.append({"k": k, "x": x, "fx": residual, "step": step,
                         "bracket": list(bounds) if a.method == "bisection" else None})
            if residual == 0:
                stop, reason = "exact", "浮点计算得到零残差；不表示一般性证明"
                break
            if a.goal == "residual" and abs(residual) <= a.tolerance:
                stop, reason = "residual", "残差达到阈值"
                break
            if a.method == "bisection" and a.goal == "root_error" and (bounds[1] - bounds[0]) / 2 <= a.tolerance:
                stop, reason = "bracket", "区间半宽达到阈值"
                break
            if a.method != "bisection" and a.goal == "root_error" and abs(residual) <= a.tolerance and len(trace) > 1:
                checked = diagnose(a.model_copy(update={"iterates": trace, "brackets": brackets, "stop_reason": "residual"}))
                if checked["complete"] and checked["status"] == "supported":
                    stop, reason = "residual", "残差达到阈值，且诊断支持要求的根误差界"
                    break
            # Never stop on a small step as if that certified root error.
            if k == request.max_iterations:
                break
            if a.method == "newton":
                derivative = f.evaluate(x, derivative=True)
                if derivative == 0:
                    reason = "导数为零，停止生成轨迹"
                    break
                x = x - (a.damping if a.variant == "damped" else a.multiplicity if a.variant == "modified" else 1) * residual / derivative
            elif a.method == "fixed_point":
                x = phi.evaluate(x)
            else:
                left, right = bounds
                bounds = (left, x) if f.evaluate(left) * residual < 0 else (x, right)
                x = (bounds[0] + bounds[1]) / 2
            if abs(x) > 1e50:
                raise ExpressionError("迭代超出数值范围")
        except (ExpressionError, ArithmeticError) as exc:
            reason = f"停止生成：{exc}"
            break
    generated = a.model_copy(update={"iterates": trace, "brackets": brackets, "stop_reason": stop})
    diagnosis = diagnose(generated)
    diagnosis["summary"] = diagnosis["summary"].replace("提交轨迹", "参考轨迹")
    return {"rows": rows, "stop_reason": stop, "stop_detail": reason,
            "diagnosis": diagnosis, "runner_version": RUNNER_VERSION,
            "evidence_kind": "reference_help", "independent_success": False}
