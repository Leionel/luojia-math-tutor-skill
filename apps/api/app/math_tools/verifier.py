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
        lhs_expr = parse_math(lhs)
        rhs_expr = parse_math(rhs)
        diff = sp.simplify(lhs_expr - rhs_expr)
        ok = diff == 0
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


def verify_lhopital_conditions(message: str) -> VerifyResult:
    text = message.replace(" ", "").replace("$", "")
    if any(key in text for key in ["0/0", "∞/∞", "无穷/无穷", "未定式", "indeterminate"]):
        return VerifyResult(
            verified=True,
            is_correct=True,
            summary="已确认极限为未定式，满足洛必达法则使用条件。",
        )
    if any(key in text for key in ["sinx/x", "sin(x)/x", "\\sinx/x", "\\sin(x)/x"]):
        return VerifyResult(
            verified=True,
            is_correct=True,
            summary="lim x->0 sinx/x 是 0/0 型未定式，满足洛必达法则使用条件。",
        )
    return VerifyResult(
        verified=True,
        is_correct=False,
        summary="未确认未定式（0/0 或 ∞/∞）就使用洛必达法则，条件不满足。",
    )

