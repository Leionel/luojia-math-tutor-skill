"""Bounded numerical experiments with domain-specific evidence, not student execution."""
import heapq
import math
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from app.math_tools.root_expression import Interval, RootExpression

Scalar = Annotated[FiniteFloat, Field(ge=-1e6, le=1e6)]
Vector = Annotated[list[Scalar], Field(min_length=2, max_length=8)]


class LinearTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domain: Literal["linear_system"] = "linear_system"
    method: Literal["jacobi", "gauss_seidel"] = "jacobi"
    matrix: list[Vector] = Field(min_length=2, max_length=8)
    rhs: Vector
    initial: Vector
    tolerance: FiniteFloat = Field(default=1e-6, ge=1e-12, le=0.1)
    limit: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def dimensions(self):
        n = len(self.matrix)
        if any(len(row) != n for row in self.matrix) or len(self.rhs) != n or len(self.initial) != n:
            raise ValueError("矩阵须为 2–8 阶方阵，向量维数须一致")
        if any(abs(self.matrix[i][i]) < 1e-12 for i in range(n)):
            raise ValueError("对角元素为零或过小，请先调整方程顺序")
        return self


class IntegrationTask(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domain: Literal["integration"] = "integration"
    method: Literal["trapezoid", "simpson", "adaptive_simpson"] = "simpson"
    expression: str = Field(default="x^2", min_length=1, max_length=200)
    left: Scalar = 0
    right: Scalar = 1
    intervals: int = Field(default=4, ge=2, le=256)
    tolerance: FiniteFloat = Field(default=1e-6, ge=1e-12, le=0.1)
    limit: int = Field(default=8, ge=1, le=100)

    @model_validator(mode="after")
    def bounds(self):
        if self.left >= self.right:
            raise ValueError("左端点必须小于右端点")
        if self.method != "trapezoid" and self.intervals % 2:
            raise ValueError("Simpson 初始分段数必须为偶数")
        return self


NumericalTask = Annotated[LinearTask | IntegrationTask, Field(discriminator="domain")]


def residual(task, vector):
    return max(abs(math.fsum(a * x for a, x in zip(row, vector)) - b)
               for row, b in zip(task.matrix, task.rhs))


def linear_reference(task):
    n = len(task.rhs)
    margins = [math.nextafter(abs(row[i]), -math.inf) - math.nextafter(math.fsum(abs(a) for j, a in enumerate(row) if j != i), math.inf)
               for i, row in enumerate(task.matrix)]
    dominant = min(margins) > 0
    conditions = ["严格行对角占优：两种迭代均有收敛的充分条件。" if dominant else
                  "未满足严格行对角占优；这不等于必然发散，需要其他收敛依据。",
                  "停止规则为绝对残差 ∥Ax−b∥∞ ≤ ε；相邻步很小不能单独证明方程已满足。",
                  "解误差界展示理论公式的浮点值，不包含残差计算的舍入误差；不是形式化误差证书。"]
    x = list(task.initial)
    rows = []
    status = "iteration_limit"
    for k in range(task.limit + 1):
        r = residual(task, x)
        if not math.isfinite(r) or max(map(abs, x)) > 1e100:
            status = "numerical_overflow"
            break
        rows.append({"k": k, "vector": x.copy(), "value": None, "residual": r,
                     "step": None if k == 0 else max(abs(a-b) for a, b in zip(x, previous)),
                     "error_estimate": None, "error_bound": r/min(margins) if dominant else None,
                     "work": k})
        if r <= task.tolerance:
            status = "residual_met"
            break
        if k == task.limit:
            break
        previous = x.copy()
        for i in range(n):
            source = previous if task.method == "jacobi" else x
            x[i] = (task.rhs[i] - math.fsum(task.matrix[i][j] * source[j] for j in range(n) if j != i)) / task.matrix[i][i]
    return {"rows": rows, "status": status, "conditions": conditions,
            "evidence_scope": "floating_point_residual", "condition_sufficient": dominant,
            "stop_detail": {"residual_met": "绝对残差已达标；不是独立学习成绩。", "iteration_limit": "达到迭代预算，残差未达标。",
                            "numerical_overflow": "数值增长超出预算，已停止。"}[status]}


def integration_reference(task):
    expression = RootExpression(task.expression)
    # Conservative interval evaluation rejects poles/domain violations, never sampling them away.
    expression.evaluate(Interval(task.left, task.right))
    cache = {}

    def f(x):
        if x not in cache:
            if len(cache) >= 8193:
                raise ValueError("超过函数求值预算")
            cache[x] = expression.evaluate(x)
        return cache[x]

    def composite(n):
        h = (task.right-task.left)/n
        endpoints = f(task.left) + f(task.right)
        if task.method == "trapezoid":
            return h*(endpoints/2 + math.fsum(f(task.left+i*h) for i in range(1, n)))
        return h/3*(endpoints + math.fsum((4 if i % 2 else 2)*f(task.left+i*h) for i in range(1, n)))

    rows = []
    status = "budget_exhausted"
    if task.method == "adaptive_simpson":
        def panel(a, b):
            m = (a+b)/2
            fa, fm, fb = f(a), f(m), f(b)
            coarse = (b-a)/6*(fa+4*fm+fb)
            fine = (b-a)/12*(fa+4*f((a+m)/2)+2*fm+4*f((m+b)/2)+fb)
            return fine, abs(fine-coarse)/15

        heap = []
        serial = 0
        value = error = 0.0
        for i in range(task.intervals//2):
            a = task.left + (task.right-task.left)*2*i/task.intervals
            b = task.left + (task.right-task.left)*2*(i+1)/task.intervals
            v, e = panel(a, b)
            heapq.heappush(heap, (-e, serial, a, b, v)); serial += 1
            value += v; error += e
        for k in range(task.limit+1):
            rows.append({"k": k, "value": value, "vector": None, "residual": None, "step": None,
                         "error_estimate": max(0.0, error), "error_bound": None, "work": len(cache)})
            if error <= task.tolerance:
                status = "estimated_tolerance_met"; break
            if k == task.limit or len(cache) + 4 > 8193:
                break
            neg_e, _, a, b, old = heapq.heappop(heap)
            middle = (a+b)/2
            new_v = new_e = 0.0
            for left, right in ((a, middle), (middle, b)):
                v, e = panel(left, right)
                heapq.heappush(heap, (-e, serial, left, right, v)); serial += 1
                new_v += v; new_e += e
            value += new_v-old; error = max(0.0, error+neg_e+new_e)
    else:
        n = task.intervals
        previous = None
        for k in range(task.limit+1):
            value = composite(n)
            estimate = None if previous is None else abs(value-previous)/(3 if task.method == "trapezoid" else 15)
            rows.append({"k": k, "value": value, "vector": None, "residual": None,
                         "step": None if previous is None else abs(value-previous),
                         "error_estimate": estimate, "error_bound": None, "work": len(cache), "intervals": n})
            if estimate is not None and estimate <= task.tolerance:
                status = "estimated_tolerance_met"; break
            if n*2 > 4096:
                break
            previous = value; n *= 2
    if not all(math.isfinite(row["value"]) for row in rows):
        raise ValueError("积分结果超出数值范围")
    return {"rows": rows, "status": status, "evidence_scope": "quadrature_error_estimate",
            "condition_sufficient": None,
            "conditions": ["误差估计依赖函数足够光滑和渐近误差模型；不是严格误差上界。",
                           "保守区间解析用于排除定义域问题；估计很小仍可能漏掉振荡或局部尖峰。"],
            "stop_detail": "误差估计达到阈值，仍需用改变分段数等方式复核。" if status == "estimated_tolerance_met" else "达到细分 / 求值预算，误差估计未达标。"}


def run_numerical(task):
    result = linear_reference(task) if isinstance(task, LinearTask) else integration_reference(task)
    return {"schema_version": "numerical-lab-v1", "task": task.model_dump(),
            "independent_success": False, "reference_help": True, **result}


def check_result(task, answer):
    if isinstance(task, LinearTask):
        if len(answer) != len(task.rhs):
            raise ValueError("答案向量维数不符")
        r = residual(task, answer)
        return {"scope": "floating_point_residual", "residual": r, "matches": r <= task.tolerance,
                "message": "只核对代入残差；不推断解题过程、独立完成或掌握度。"}
    if len(answer) != 1:
        raise ValueError("积分结果须为一个数值")
    reference = integration_reference(task)
    difference = abs(answer[0] - reference["rows"][-1]["value"])
    return {"scope": "reference_agreement_only", "difference": difference,
            "matches": difference <= task.tolerance,
            "message": "只比较本次数值参考结果；相符不代表真实积分误差达标。"}
