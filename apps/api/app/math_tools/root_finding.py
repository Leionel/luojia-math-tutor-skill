"""root-oracle-v1: inspect submitted traces; never execute submitted programs."""
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.math_tools.root_expression import ExpressionError, Interval, RootExpression

ORACLE_VERSION = "root-oracle-v1"
TOLERANCE_VERSION = "root-tolerance-v1"
FAMILIES = {
    "newton_formula": "CASE_NEWTON_CODE_UPDATE",
    "newton_derivative_zero": "CASE_NEWTON_DERIVATIVE_ZERO",
    "newton_cycle": "CASE_NEWTON_INITIAL_VALUE",
    "newton_stop_step": "CASE_NEWTON_CODE_STOPPING",
    "residual_without_error_bound": "CASE_RESIDUAL_VS_ERROR",
    "bisection_bracket": "CASE_BISECTION_REQUIREMENTS",
    "bisection_update": "CASE_BISECTION_BRACKET_UPDATE",
    "bisection_stop": "CASE_BISECTION_ERROR_BOUND",
    "fixed_point_update": "CASE_FIXED_POINT_DIVERGENCE",
    "fixed_point_conditions": "CASE_FIXED_POINT_CONTRACTION",
    "numeric_nonfinite": "CASE_STOPPING_CRITERION",
    "iteration_limit": "CASE_STOPPING_CRITERION",
}


class RootAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    method: Literal["newton", "bisection", "fixed_point"]
    function: str = Field(min_length=1, max_length=200)
    iterates: list[float | Literal["NaN", "Inf", "-Inf"]] = Field(default_factory=list, max_length=101)
    brackets: list[tuple[float, float]] = Field(default_factory=list, max_length=101)
    interval: tuple[float, float] | None = None
    initial_value: float | None = None
    phi: str | None = Field(default=None, max_length=200)
    derivative: str | None = Field(default=None, max_length=200)
    update: str | None = Field(default=None, max_length=200)
    variant: Literal["standard", "damped", "modified"] = "standard"
    damping: float = Field(default=1.0, gt=0, le=1)
    multiplicity: int = Field(default=1, ge=1, le=10)
    tolerance: float = Field(default=1e-6, ge=1e-12, le=0.01)
    goal: Literal["root_error", "residual"] = "root_error"
    stop_reason: Literal["none", "residual", "step", "bracket", "exact", "iteration_limit"] = "none"

    @model_validator(mode="after")
    def bounded_numbers(self):
        nums = [v for v in self.iterates if isinstance(v, (float, int))]
        nums += [v for pair in self.brackets + ([self.interval] if self.interval else []) for v in pair]
        if self.initial_value is not None: nums.append(self.initial_value)
        if any(not math.isfinite(v) or abs(v) > 1e50 for v in nums):
            raise ValueError("轨迹数值须有限且绝对值不超过 1e50；非有限观察用 NaN/Inf 字符串")
        return self


def _close(a, b):
    return math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-10)


def diagnose(attempt: RootAttempt) -> dict:
    rows: list[dict] = []

    def result(status, family, summary, probe, step=None, *, complete=False, evidence=None):
        return {"status": status, "family": family, "summary": summary,
                "next_probe": probe, "error_step": step, "complete": complete,
                "oracle_version": ORACLE_VERSION, "tolerance_version": TOLERANCE_VERSION,
                "tolerance": attempt.tolerance, "goal": attempt.goal,
                "trace": rows, "evidence": evidence or {},
                "hypothesis": family, "action": "revise" if status == "contradicted" else "ask_conditions" if status == "inconclusive" else "confirm" if complete else "continue",
                "case_hint": FAMILIES.get(family)}

    try:
        f = RootExpression(attempt.function)
        if not attempt.iterates and not attempt.brackets:
            return result("inconclusive", "missing_trace", "尚未提交迭代轨迹，不能定位过程错误。", "补充至少两个相邻迭代值，或二分区间更新记录。")
        if any(isinstance(v, str) for v in attempt.iterates):
            index = next(i for i, v in enumerate(attempt.iterates) if isinstance(v, str))
            return result("contradicted", "numeric_nonfinite", "轨迹出现非有限数值；这一轮没有有效的根近似。", "检查该步分母、定义域和溢出保护。", index, evidence={"observed": attempt.iterates[index]})
        xs = [float(x) for x in attempt.iterates]
        for k, x in enumerate(xs):
            try:
                fx = f.evaluate(x)
            except ExpressionError:
                return result("contradicted", "numeric_nonfinite", "此步无法在函数定义域内得到有限值。", "检查表达式定义域及该步输入。", k, evidence={"x": x})
            rows.append({"k": k, "x_k": x, "f_x": fx, "step_size": abs(x - xs[k - 1]) if k else None,
                         "finite_flag": True, "stop_reason": attempt.stop_reason if k == len(xs) - 1 else "none"})
        if attempt.initial_value is not None and (not xs or not _close(xs[0], attempt.initial_value)):
            return result("contradicted", "initial_value", "轨迹初值与任务初值不一致。", "从任务规定的初值重新提交轨迹。", 0)
        certified_interval = None
        if attempt.method == "bisection":
            brackets = attempt.brackets or ([attempt.interval] if attempt.interval else [])
            if not brackets:
                return result("inconclusive", "bisection_bracket", "二分法需要初始区间和更新后的区间。", "给出 [a,b] 及端点更新记录。")
            previous = None
            for k, (a, b) in enumerate(brackets):
                if a >= b:
                    return result("contradicted", "bisection_bracket", "区间端点顺序不正确。", "保证 a < b。", k)
                try:
                    f.evaluate(Interval(a, b))
                    fa, fb = f.evaluate(a), f.evaluate(b)
                except ExpressionError:
                    return result("inconclusive", "bisection_bracket", "区间运算不能确认此区间上函数连续；端点变号不足以保证有根。", "检查是否跨过分母零点或定义域边界。", k)
                if fa * fb > 0:
                    return result("contradicted", "bisection_bracket" if k == 0 else "bisection_update", "区间两端同号，不能作为已确认的二分有根区间。", "重新检查端点符号，保留包含零点的半区间。", k, evidence={"f_a": fa, "f_b": fb})
                if previous:
                    pa, pb = previous
                    c = pa + (pb - pa) / 2
                    left = _close(a, pa) and _close(b, c)
                    right = _close(a, c) and _close(b, pb)
                    if not (left or right):
                        return result("contradicted", "bisection_update", "更新区间不是前一区间的一半。", "用中点替换一个端点，再检查变号不变量。", k)
                previous = (a, b)
            certified_interval = brackets[-1]
            a, b = certified_interval
            x = xs[-1] if xs else a + (b - a) / 2
            if not a <= x <= b:
                return result("contradicted", "bisection_update", "提交的近似值不在最终区间内。", "核对最终区间与近似值。", len(rows) - 1)
            if not rows:
                rows.append({"k": len(brackets) - 1, "x_k": x, "f_x": f.evaluate(x), "step_size": None, "bracket": [a, b], "finite_flag": True, "stop_reason": attempt.stop_reason})
            bound = max(x - a, b - x)
            if f.evaluate(a) == 0 or f.evaluate(b) == 0:
                bound = abs(x - (a if f.evaluate(a) == 0 else b))
            for row in rows:
                row["bracket"] = list(brackets[min(row["k"], len(brackets) - 1)])
            if attempt.stop_reason == "bracket" and bound > attempt.tolerance:
                return result("contradicted", "bisection_stop", "最终区间给出的误差上界尚大于容差。", "再缩小区间；中点误差上界是区间长度的一半。", len(brackets) - 1, evidence={"error_bound": bound})
            if attempt.goal == "root_error" and bound <= attempt.tolerance:
                return result("supported", "valid", "区间不变量和提交的误差上界满足要求。", "可用一道不同函数的独立探针检查方法。", complete=True, evidence={"error_bound": bound})
        else:
            if not xs:
                return result("inconclusive", "missing_trace", "需要至少一个迭代值。", "提交 x0、x1 等轨迹。")
            phi = RootExpression(attempt.phi) if attempt.phi else None
            derivative = RootExpression(attempt.derivative) if attempt.derivative else None
            update = RootExpression(attempt.update, update=True) if attempt.update else None
            if attempt.method == "fixed_point" and not phi:
                return result("inconclusive", "fixed_point_conditions", "尚未提供迭代函数 g(x)。", "给出 g(x)、初值与收敛区间。")
            for k in range(len(xs) - 1):
                x, fx = xs[k], rows[k]["f_x"]
                if attempt.method == "newton":
                    try: df = f.evaluate(x, derivative=True)
                    except ExpressionError:
                        return result("inconclusive", "newton_derivative_zero", "此点导数不可确认，不能直接使用普通 Newton 更新。", "核对可微性或换用有区间保护的方法。", k)
                    if abs(df) <= 1e-12 and abs(fx) > attempt.tolerance:
                        return result("contradicted", "newton_derivative_zero", "导数为零或过小，普通 Newton 商不能安全计算。", "检查初值及导数保护，必要时采用二分保护。", k, evidence={"derivative": df, "f_x": fx})
                    if abs(fx) <= 1e-14 and abs(df) <= 1e-12:
                        return result("inconclusive", "newton_derivative_zero", "该点可能已经是根，但不能继续做 0/0 更新。", "先检查残差，再决定是否需要更新。", k)
                    if derivative and not _close(derivative.evaluate(x), df):
                        return result("contradicted", "newton_formula", "提交的导数与函数在该点的导数不一致。", "重新求导后再算这一步。", k, evidence={"observed_derivative": derivative.evaluate(x), "reference_derivative": df})
                    factor = attempt.damping if attempt.variant == "damped" else attempt.multiplicity if attempt.variant == "modified" else 1
                    expected = x - factor * fx / df
                    if update and not _close(update.evaluate(x, f=fx, df=df), expected):
                        return result("contradicted", "newton_formula", "提交的更新公式与普通 Newton 步不一致。", "检查商的分子、分母和减号；如用阻尼或改进法，请注明。", k)
                    family = "newton_formula"
                else:
                    expected, family = phi.evaluate(x), "fixed_point_update"
                if not _close(xs[k + 1], expected):
                    return result("contradicted", family, "相邻迭代值不满足所声明的更新规则。", "从定位到的这一步重新计算；如采用另一种方法，请明确声明。", k + 1, evidence={"observed": xs[k + 1], "reference_step": expected})
            if len(xs) >= 3 and _close(xs[-1], xs[-3]) and not _close(xs[-1], xs[-2]) and abs(rows[-1]["f_x"]) > attempt.tolerance:
                return result("contradicted", "newton_cycle" if attempt.method == "newton" else "fixed_point_conditions", "轨迹在两个值之间循环，尚未收敛。", "检查初值或迭代格式，考虑带区间保护的方法。", len(xs) - 1)
            if attempt.method == "fixed_point" and attempt.interval:
                a, b = attempt.interval
                try:
                    image = phi.evaluate(Interval(a, b))
                    slope = phi.evaluate(Interval(a, b), derivative=True)
                    q = max(abs(slope.lo), abs(slope.hi))
                    # Rounded interval arithmetic can be conservative: failure to certify is not divergence.
                    if image.lo >= a and image.hi <= b and q < 1 and all(a <= x <= b for x in xs) and len(xs) > 1:
                        bound = q / (1 - q) * abs(xs[-1] - xs[-2])
                        if attempt.goal == "residual" and bound <= attempt.tolerance and abs(rows[-1]["f_x"]) <= attempt.tolerance:
                            return result("supported", "valid", "压缩界支持 g 的不动点误差，f 的残差满足所指定目标；未据此断言 f 的根误差。", "需要 f 的根误差时请提供有根区间与导数下界。", complete=True, evidence={"q_bound": q, "fixed_point_error_bound": bound})
                except ExpressionError:
                    pass
            certified_interval = attempt.interval
        last = rows[-1]
        if attempt.stop_reason == "iteration_limit":
            return result("inconclusive", "iteration_limit", "达到迭代上限只代表停止计算，不能记为成功。", "检查残差、区间或误差界后再判断。", last["k"])
        residual = abs(last["f_x"])
        if attempt.goal == "residual" and residual <= attempt.tolerance:
            return result("supported", "valid", "提交轨迹通过，最终残差满足所指定目标；没有据此断言根误差。", "需要根误差时请另给可验证误差界。", complete=True, evidence={"residual": residual})
        error_bound = None
        if certified_interval:
            a, b = certified_interval
            try:
                f.evaluate(Interval(a, b))
                slope = f.evaluate(Interval(a, b), derivative=True)
                lower = min(abs(slope.lo), abs(slope.hi)) if slope.lo * slope.hi > 0 else 0
                if a <= last["x_k"] <= b and f.evaluate(a) * f.evaluate(b) <= 0 and lower > 1e-12:
                    error_bound = residual / lower
            except ExpressionError:
                pass
        if error_bound is not None and error_bound <= attempt.tolerance:
            return result("supported", "valid", "有根区间及导数下界支持所提交的根误差目标。", "可进行独立探针。", complete=True, evidence={"residual": residual, "error_bound": error_bound})
        if attempt.stop_reason == "step" and residual > attempt.tolerance:
            return result("contradicted", "newton_stop_step" if attempt.method == "newton" else "fixed_point_conditions", "步长小并未同时保证残差满足目标。", "同时检查残差和可用误差界，不把停机等同成功。", last["k"], evidence={"residual": residual})
        if residual <= attempt.tolerance or attempt.stop_reason in ("residual", "exact"):
            return result("inconclusive", "residual_without_error_bound", "残差信息尚不能确认要求的根误差。", "给出有根区间和导数下界，或明确只要求残差容差。", last["k"], evidence={"residual": residual, "error_bound": error_bound})
        if attempt.method == "fixed_point":
            return result("inconclusive", "fixed_point_conditions", "轨迹符合更新式，但当前区间条件未能支持收敛或求根完成。", "检查 g(I)⊆I 与 |g'| 上界；未确认条件不等同已经发散。")
        return result("supported", "valid", "已提交步骤符合更新规则；尚未确认完成求根。", "继续提交轨迹及停止依据。", evidence={"residual": residual})
    except ExpressionError:
        return result("inconclusive", "unsupported_expression", "表达式超出受控语法或无法确认数值条件；没有执行学生代码。", "使用 x、整数幂及 sin/cos/tan/exp/log/sqrt/abs，并检查定义域。")
    except Exception:
        return result("tool_error", "oracle_failure", "数值验证暂不可用；本轮结果未知。", "保留轨迹，稍后重试或请教师核对。")
