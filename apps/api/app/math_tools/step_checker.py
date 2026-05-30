import re

from app.math_tools.verifier import (
    VerifyResult,
    verify_derivative,
    verify_determinant_2x2,
    verify_integral,
    verify_lhopital_conditions,
)
from app.tutor.misconception import Mistake, detect_mistake


def _extract_integral_attempt(text: str) -> tuple[str, str] | None:
    compact = text.replace(" ", "")
    match = re.search(r"∫([^=]+)dx=([^，。\n]+)", compact)
    if match:
        return match.group(1), match.group(2)
    match = re.search(r"\\int([^=]+)dx=([^，。\n]+)", compact)
    if match:
        return match.group(1), match.group(2)
    return None


def _extract_derivative_request(text: str) -> tuple[str, str] | None:
    compact = text.replace(" ", "")
    patterns = [
        r"d/dx\s*([^=，。\n]+)",
        r"求导\s*([^=，。\n]+)",
        r"求\s*d/dx\s*([^=，。\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact)
        if match:
            expr = match.group(1)
            expected = None
            if "=" in text:
                expected = text.split("=")[-1].strip()
            return expr, expected or ""
    return None


def _extract_determinant_attempt(text: str) -> tuple[list[list[float]], str] | None:
    compact = text.replace(" ", "").replace("$", "")
    match = re.search(r"\|(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?);\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\|", compact)
    if match:
        a, b, c, d = map(float, match.groups())
        return [[a, b], [c, d]], ""
    match = re.search(r"begin\{pmatrix\}(-?\d+(?:\.\d+)?)&(-?\d+(?:\.\d+)?)\\\\(-?\d+(?:\.\d+)?)&(-?\d+(?:\.\d+)?)\\end\{pmatrix\}", compact)
    if match:
        a, b, c, d = map(float, match.groups())
        return [[a, b], [c, d]], ""
    return None


def check_step(message: str) -> tuple[VerifyResult, Mistake | None]:
    integral = _extract_integral_attempt(message)
    if integral:
        integrand, candidate = integral
        result = verify_integral(integrand, "x", candidate)
        return result, detect_mistake(message, result.summary)

    derivative = _extract_derivative_request(message)
    if derivative:
        expr, expected = derivative
        if expected:
            result = verify_derivative(expr, "x", expected)
            return result, detect_mistake(message, result.summary)
        else:
            try:
                import sympy as sp
                derivative_expr = sp.diff(expr, sp.Symbol("x"))
                result = VerifyResult(
                    verified=True,
                    is_correct=True,
                    summary=f"求导结果为 {sp.sstr(derivative_expr)}。",
                    actual=sp.sstr(derivative_expr),
                )
                return result, detect_mistake(message, result.summary)
            except Exception as exc:
                return VerifyResult(False, None, f"求导处理失败：{exc}"), None

    determinant = _extract_determinant_attempt(message)
    if determinant:
        matrix, candidate = determinant
        result = verify_determinant_2x2(matrix, candidate or str(matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]))
        return result, detect_mistake(message, result.summary)

    if any(key in message for key in ["洛必达", "lhopital", "L'Hopital"]):
        result = verify_lhopital_conditions(message)
        return result, detect_mistake(message, result.summary)

    mistake = detect_mistake(message)
    if mistake:
        return VerifyResult(True, False, mistake.label), mistake
    return VerifyResult(False, None, "未识别到可自动验证的单步推导。"), None

