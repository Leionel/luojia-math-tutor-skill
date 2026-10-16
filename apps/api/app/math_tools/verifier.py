"""Scoped deterministic checks. Public requests execute these in the fixed worker."""
from dataclasses import dataclass, field
import math
import re

import sympy as sp
from app.math_tools.safe_symbolic import MathSyntaxError, math_tree, normalize_math, parse_bounded

CHECKER_VERSION = "step-v1"


@dataclass
class VerifyResult:
    verified: bool
    is_correct: bool | None
    summary: str
    details: str = ""
    expected: str | None = None
    actual: str | None = None
    version: str = CHECKER_VERSION
    execution_status: str = "not_requested"
    origin: str = "none"
    scope: str = "none"
    assumptions: list[str] = field(default_factory=list)
    scope_complete: bool = False
    input_hash: str | None = None
    candidate_hash: str | None = None
    eligible_learning_evidence: bool = False
    unknown_reason: str = ""

    def public(self):
        return {key: getattr(self, key) for key in (
            "version", "execution_status", "origin", "scope", "assumptions", "scope_complete",
            "input_hash", "candidate_hash", "eligible_learning_evidence", "unknown_reason")}


def parse_math(expr: str) -> sp.Expr:
    # Compatibility helper; construction uses a finite AST, never parse_expr/sympify(str).
    return parse_bounded(expr)[0]


def _unknown(reason, scope="none", *, status="rejected"):
    return VerifyResult(False, None, "本步自动核验未确定：" + reason + "；不会据此判学生错误。",
                        execution_status=status, scope=scope, unknown_reason=reason)


def _condition_text(condition):
    if hasattr(condition, "rel_op"):
        return f"{condition.lhs} {'≠' if condition.rel_op == '!=' else condition.rel_op} {condition.rhs}"
    return str(condition)


def _checked(left, right, conditions, scope, *, expected=None, actual=None):
    conditions = list(dict.fromkeys(conditions))
    diff = sp.simplify(left - right)
    ok = True if diff == 0 or diff.is_zero is True else None
    witness = ""
    if ok is None:
        x = sp.Symbol("x", real=True)
        for point in (sp.Integer(0), sp.Integer(1), sp.Integer(-1), sp.Integer(2), sp.Integer(-2), sp.Rational(1, 2)):
            if not all(condition.subs(x, point) is sp.true for condition in conditions):
                continue
            value = sp.simplify(diff.subs(x, point))
            if not value.has(sp.zoo, sp.nan, sp.oo, -sp.oo) and value.is_zero is False:
                ok, witness = False, f"实数见证 x={point}，差为 {value}"
                break
    assumptions = ["x为实数；只核对所述表达式/操作，不证明整题。"] + [_condition_text(c) for c in conditions]
    if ok is None:
        result = _unknown("未能确定等价或找到有效差异见证", scope, status="succeeded")
        result.assumptions = assumptions
        return result
    result = VerifyResult(True, ok, "核验通过。" if ok else "核验不通过。",
                          details=witness or str(diff), expected=expected, actual=actual,
                          execution_status="succeeded", scope=scope, assumptions=assumptions,
                          scope_complete=not conditions)
    return result


def verify_equivalent(lhs: str, rhs: str) -> VerifyResult:
    try:
        left, lc = parse_bounded(lhs)
        right, rc = parse_bounded(rhs)
        result = _checked(left, right, lc + rc, "expression_equivalence")
        if result.verified:
            result.summary = ("两个表达式在共同实数定义域内等价。" if result.is_correct else "两个表达式在共同实数定义域内不等价。")
            if lc or rc:
                result.summary += " 原式条件/排除点：" + "; ".join(map(_condition_text, dict.fromkeys(lc + rc))) + "；未核对全域同定义域的主张。"
        return result
    except Exception:
        return _unknown("表达式超出受控语法或定义域", "expression_equivalence")


def verify_derivative(expr: str, variable: str, expected: str | None) -> VerifyResult:
    if variable != "x":
        return _unknown("首版只支持实数单变量x", "derivative")
    try:
        value, conditions = parse_bounded(expr, derivative=True)
        derivative = sp.diff(value, sp.Symbol("x", real=True))
        if len(str(derivative)) > 8192:
            raise MathSyntaxError("output_budget")
        if expected is None:
            return VerifyResult(False, None, f"已计算参考导数 {derivative}；没有学生候选，未核对学生答案。",
                                actual=str(derivative), execution_status="succeeded", origin="system_calculation",
                                scope="derivative", assumptions=["x为实数，仅在原式有定义且可微的区域适用。"] + list(map(_condition_text, conditions)))
        candidate, cc = parse_bounded(expected)
        result = _checked(derivative, candidate, conditions + cc, "derivative", expected=str(candidate), actual=str(derivative))
        if result.verified:
            result.summary = f"求导验证{'通过' if result.is_correct else '不通过'}，实际导数为 {derivative}。"
            if conditions or cc: result.summary += " 仅在条件 " + "; ".join(map(_condition_text, dict.fromkeys(conditions + cc))) + " 下适用。"
        return result
    except Exception:
        return _unknown("求导输入超出受控语法或实数可微范围", "derivative")


def verify_integral(integrand: str, variable: str, candidate: str) -> VerifyResult:
    if variable != "x": return _unknown("首版只支持实数单变量x", "integral_candidate")
    try:
        value, conditions = parse_bounded(candidate, allow_constant=True, derivative=True)
        derivative = sp.diff(value, sp.Symbol("x", real=True))
        target, tc = parse_bounded(integrand)
        result = _checked(derivative, target, conditions + tc, "integral_candidate", expected=str(target), actual=str(derivative))
        if result.verified:
            result.summary = f"积分候选验证{'通过' if result.is_correct else '不通过'}，对候选求导得到 {derivative}，被积函数为 {target}；只检查反导数候选，不核对一般通解/积分常数。"
        return result
    except Exception:
        return _unknown("积分候选超出受控语法或实数可微范围", "integral_candidate")


def _matrix(value):
    if not isinstance(value, list) or not 1 <= len(value) <= 8:
        raise ValueError("matrix_budget")
    columns = len(value[0]) if isinstance(value[0], list) else 0
    if not 1 <= columns <= 8 or any(not isinstance(row, list) or len(row) != columns for row in value):
        raise ValueError("matrix_shape")
    if any(type(n) not in {int, float} or abs(n) > 1e12 or not math.isfinite(n) for row in value for n in row):
        raise ValueError("matrix_numbers")
    return sp.Matrix([[sp.Rational(str(n)) for n in row] for row in value])


def compute_matrix_product(left, right) -> VerifyResult:
    try:
        value = _matrix(left) * _matrix(right)
        return VerifyResult(False, None, f"参考矩阵乘法结果为 {value.tolist()}；没有学生候选。", actual=str(value.tolist()),
                            origin="system_calculation", execution_status="succeeded", scope="matrix_product")
    except Exception:
        return _unknown("矩阵输入无效或超出预算", "matrix_product")


def verify_determinant_2x2(matrix, candidate: str | None) -> VerifyResult:
    try:
        value = _matrix(matrix)
        if value.shape != (2, 2): raise ValueError("matrix_shape")
        target = value.det()
        if candidate is None:
            return VerifyResult(False, None, f"参考行列式值为 {target}；没有学生候选。", actual=str(target),
                                origin="system_calculation", execution_status="succeeded", scope="determinant_2x2")
        answer, conditions = parse_bounded(candidate)
        if answer.free_symbols: raise ValueError("numeric_candidate_required")
        result = _checked(target, answer, conditions, "determinant_2x2", expected=str(target), actual=str(answer))
        if result.verified: result.summary = f"二阶行列式验证{'通过' if result.is_correct else '不通过'}，正确值为 {target}。"
        return result
    except Exception:
        return _unknown("行列式或候选输入不受支持", "determinant_2x2")


_LIMIT_HEADING = re.compile(r"lim(?:it)?\s*(?:_\{?\s*)?(?P<var>[a-zA-Z])\s*(?:\\to|->|→)\s*(?P<point>[^\s,，;；]+)\s*\}?\s*[:：]?\s*(?P<expr>[^;；\n]+)", re.IGNORECASE)


def verify_lhopital_conditions(message: str) -> VerifyResult:
    """Only classify an unsimplified quotient's form, never certify L'Hopital."""
    match = _LIMIT_HEADING.search(message)
    if not match or match['var'] != 'x':
        return _unknown("无法解析受支持的单变量极限，未核对洛必达条件", "indeterminate_form")
    try:
        expr_text = re.split(r"[\u4e00-\u9fff，。！？?]", match['expr'], maxsplit=1)[0].strip()
        tree = math_tree(expr_text)
        import ast
        if not isinstance(tree.body, ast.BinOp) or not isinstance(tree.body.op, ast.Div):
            raise ValueError("explicit_quotient_required")
        from app.math_tools.safe_symbolic import construct_math
        # Keep numerator and denominator separate before any cancellation.
        num, _ = construct_math(ast.Expression(tree.body.left))
        den, _ = construct_math(ast.Expression(tree.body.right))
        point_text = match['point'].strip("})）").replace(r"\infty", "oo").replace("∞", "oo")
        point = {"oo": sp.oo, "+oo": sp.oo, "-oo": -sp.oo}.get(point_text)
        if point is None:
            point = parse_math(point_text)
            if point.free_symbols: raise ValueError("numeric_point_required")
        x = sp.Symbol("x", real=True)
        n, d = sp.limit(num, x, point), sp.limit(den, x, point)
        form = "0/0" if n == 0 and d == 0 else "∞/∞" if sp.Abs(n) == sp.oo and sp.Abs(d) == sp.oo else None
        result = VerifyResult(True, None if form else False,
                              f"已检查分子极限为 {n}、分母极限为 {d}；" +
                              (f"属于 {form} 型未定式；" if form else "不是0/0或∞/∞型未定式，不满足该必要条件；") +
                              "仅核对未定式分类，未核对可导性、分母导数非零及导数比极限，不能确认洛必达法则适用。",
                              actual=form, origin="classification", execution_status="succeeded", scope="indeterminate_form",
                              assumptions=["x为实数；仅计算默认右侧/无穷极限，未确认双侧定理条件。"],
                              unknown_reason="theorem_conditions_not_checked" if form else "")
        return result
    except Exception:
        return _unknown("极限表达式或求极限不受支持；未核对洛必达条件", "indeterminate_form")
