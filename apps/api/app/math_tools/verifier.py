from dataclasses import dataclass
import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)


@dataclass
class VerifyResult:
    verified: bool
    is_correct: bool | None
    summary: str
    details: str = ""
    expected: str | None = None
    actual: str | None = None


def normalize_math(text: str) -> str:
    text = text.strip()
    text = text.replace("$", "")
    text = text.replace("\\left", "").replace("\\right", "")
    replacements = {
        "\\cdot": "*",
        "\\times": "*",
        "\\pi": "pi",
        "\\sin": "sin",
        "\\cos": "cos",
        "\\tan": "tan",
        "\\ln": "log",
        "\\sqrt": "sqrt",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Convert Unicode superscript digits to ^ notation for SymPy compatibility
    superscript_map = {
        "¹": "1", "²": "2", "³": "3",
        "⁴": "4", "⁵": "5", "⁶": "6",
        "⁷": "7", "⁸": "8", "⁹": "9", "⁰": "0",
        "⁻": "-",
    }
    for uni, ascii_digit in superscript_map.items():
        text = text.replace(uni, "^" + ascii_digit)
    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"((\1)/(\2))", text)
    text = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", text)
    text = text.replace("{", "(").replace("}", ")")
    text = text.replace("，", ",")
    return text


def parse_math(expr: str) -> sp.Expr:
    normalized = normalize_math(expr)
    return parse_expr(normalized, transformations=TRANSFORMS, evaluate=True)


def verify_equivalent(lhs: str, rhs: str) -> VerifyResult:
    try:
        lhs_expr = sp.nsimplify(parse_math(lhs), rational=True)
        rhs_expr = sp.nsimplify(parse_math(rhs), rational=True)
        diff = sp.simplify(lhs_expr - rhs_expr)
        equals = lhs_expr.equals(rhs_expr)
        ok = diff == 0 or equals is True
        return VerifyResult(
            verified=True,
            is_correct=bool(ok),
            summary="两个表达式等价。" if ok else f"两个表达式不等价，化简差为 {sp.sstr(diff)}。",
            details=sp.sstr(diff),
        )
    except Exception as exc:
        return VerifyResult(False, None, f"表达式等价验证失败：{exc}")


def verify_derivative(expr: str, variable: str, expected: str) -> VerifyResult:
    try:
        var = sp.Symbol(variable)
        derivative = sp.diff(parse_math(expr), var)
        expected_expr = parse_math(expected)
        diff = sp.simplify(derivative - expected_expr)
        ok = diff == 0
        return VerifyResult(
            verified=True,
            is_correct=bool(ok),
            summary=(
                f"求导验证通过，导数为 {sp.sstr(derivative)}。"
                if ok
                else f"求导验证不通过，实际导数为 {sp.sstr(derivative)}。"
            ),
            expected=sp.sstr(expected_expr),
            actual=sp.sstr(derivative),
        )
    except Exception as exc:
        return VerifyResult(False, None, f"求导验证失败：{exc}")


def verify_integral(integrand: str, variable: str, candidate: str) -> VerifyResult:
    try:
        var = sp.Symbol(variable)
        clean_candidate = re.sub(r"\+?\s*C\b", "", candidate)
        derivative = sp.diff(parse_math(clean_candidate), var)
        integrand_expr = parse_math(integrand)
        diff = sp.simplify(derivative - integrand_expr)
        ok = diff == 0
        return VerifyResult(
            verified=True,
            is_correct=bool(ok),
            summary=(
                f"积分候选验证通过，对候选结果求导得到 {sp.sstr(derivative)}。"
                if ok
                else f"积分候选验证不通过，对候选结果求导得到 {sp.sstr(derivative)}，不是 {sp.sstr(integrand_expr)}。"
            ),
            expected=sp.sstr(integrand_expr),
            actual=sp.sstr(derivative),
        )
    except Exception as exc:
        return VerifyResult(False, None, f"积分验证失败：{exc}")


def compute_matrix_product(left: list[list[float]], right: list[list[float]]) -> VerifyResult:
    try:
        result = sp.Matrix(left) * sp.Matrix(right)
        return VerifyResult(True, True, f"矩阵乘法结果为 {result.tolist()}。", actual=str(result.tolist()))
    except Exception as exc:
        return VerifyResult(False, None, f"矩阵计算失败：{exc}")


def verify_determinant_2x2(matrix: list[list[float]], candidate: str) -> VerifyResult:
    try:
        a, b, c, d = matrix[0][0], matrix[0][1], matrix[1][0], matrix[1][1]
        expected_val = a * d - b * c
        expected_expr = sp.simplify(expected_val)
        candidate_expr = parse_math(candidate)
        diff = sp.simplify(candidate_expr - expected_expr)
        ok = diff == 0
        return VerifyResult(
            verified=True,
            is_correct=bool(ok),
            summary=(
                f"二阶行列式验证通过，值为 {expected_expr}。"
                if ok
                else f"二阶行列式验证不通过，正确值应为 {expected_expr}。"
            ),
            expected=str(expected_expr),
            actual=str(candidate_expr),
        )
    except Exception as exc:
        return VerifyResult(False, None, f"行列式验证失败：{exc}")


_LIMIT_HEADING = re.compile(
    r"lim(?:it)?\s*(?:_\{?\s*)?(?P<var>[a-zA-Z])\s*(?:\\to|->|→)\s*(?P<point>[^\s,，;；]+)\s*\}?\s*[:：]?\s*(?P<expr>[^;；\n]+)",
    re.IGNORECASE,
)

# Keyword mentions only mark a candidate for symbolic checking; they can never
# decide the outcome by themselves.
_CJK_TOKEN = re.compile(r"[\u4e00-\u9fff，。！？：；、（）]")


def _prepare_expr_text(text: str) -> str:
    # Implicit multiplication cannot turn "sinx" into sin(x), so expand the
    # common compact forms before parsing. The lookahead stops at ASCII
    # letters only, so Chinese text directly after the x still matches.
    text = re.sub(r"sin\s*x(?![a-zA-Z])", "sin(x)", text)
    text = re.sub(r"cos\s*x(?![a-zA-Z])", "cos(x)", text)
    text = re.sub(r"tan\s*x(?![a-zA-Z])", "tan(x)", text)
    return text


def _parse_prefix_candidate(expr_text: str) -> sp.Expr | None:
    """Parse the leading math tokens of free-text trailing a limit heading.

    Trailing natural-language tokens (which may contain the student's own
    "0/0" claim) are excluded: only the expression itself may be parsed.
    """
    math_tokens: list[str] = []
    for token in expr_text.split():
        if _CJK_TOKEN.search(token):
            break
        math_tokens.append(token)
    for end in range(len(math_tokens), 0, -1):
        candidate = _prepare_expr_text(" ".join(math_tokens[:end]))
        if not candidate.strip():
            continue
        try:
            return parse_math(candidate)
        except Exception:
            continue
    return None


def _classify_indeterminate(
    expr: sp.Expr,
    var_name: str,
    point_text: str,
) -> tuple[str | None, str, str]:
    """Compute the numerator/denominator limits and classify the form.

    Returns (form, num_limit_str, den_limit_str); form is None when the
    limit is not an indeterminate 0/0 or ∞/∞ form (or cannot be computed).
    """
    x = sp.Symbol(var_name)
    cleaned_point = point_text.lstrip("+").replace("∞", "oo").replace("\\infty", "oo").replace("infty", "oo")
    point = parse_math(cleaned_point) if cleaned_point != "oo" else sp.oo
    num, den = sp.fraction(sp.together(expr))
    num_lim = sp.limit(num, x, point)
    den_lim = sp.limit(den, x, point)

    num_zero = sp.simplify(num_lim) == 0
    den_zero = sp.simplify(den_lim) == 0
    num_inf = sp.Abs(num_lim) == sp.oo
    den_inf = sp.Abs(den_lim) == sp.oo

    if num_zero and den_zero:
        return "0/0", sp.sstr(num_lim), sp.sstr(den_lim)
    if num_inf and den_inf:
        return "∞/∞", sp.sstr(num_lim), sp.sstr(den_lim)
    return None, sp.sstr(num_lim), sp.sstr(den_lim)


def verify_lhopital_conditions(message: str) -> VerifyResult:
    """Deterministically decide whether the limit in `message` is indeterminate.

    The decision is made by SymPy limit evaluation on the expression found in
    the message. Keyword mentions like "0/0" only indicate that a check is
    being requested; they never substitute for the symbolic verdict.
    """
    match = _LIMIT_HEADING.search(message)
    if not match:
        return VerifyResult(
            verified=False,
            is_correct=None,
            summary=(
                "未能在消息中解析出形如 lim x->a f(x) 的极限表达式，"
                "无法确定性判定未定式类型，不能据此确认洛必达法则的使用条件。"
            ),
        )

    var_name = match.group("var")
    point_text = match.group("point").strip("）)")
    try:
        expr = _parse_prefix_candidate(match.group("expr"))
        if expr is None:
            raise ValueError("expression parse failed")
        form, num_lim, den_lim = _classify_indeterminate(expr, var_name, point_text)
    except Exception as exc:
        return VerifyResult(
            verified=False,
            is_correct=None,
            summary=f"极限表达式解析或求极限失败，无法判定未定式类型：{exc}",
        )

    if form == "0/0":
        return VerifyResult(
            verified=True,
            is_correct=True,
            summary=(
                f"SymPy 计算分子极限为 {num_lim}、分母极限为 {den_lim}，"
                "属于 0/0 型未定式，满足洛必达法则使用条件。"
            ),
        )
    if form == "∞/∞":
        return VerifyResult(
            verified=True,
            is_correct=True,
            summary=(
                f"SymPy 计算分子极限为 {num_lim}、分母极限为 {den_lim}，"
                "属于 ∞/∞ 型未定式，满足洛必达法则使用条件。"
            ),
        )
    return VerifyResult(
        verified=True,
        is_correct=False,
        summary=(
            f"SymPy 计算分子极限为 {num_lim}、分母极限为 {den_lim}，"
            "该极限不是 0/0 或 ∞/∞ 型未定式，不满足洛必达法则使用条件。"
        ),
    )
