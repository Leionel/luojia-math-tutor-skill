"""Extract a bounded student claim and bind the scoped checker to its source."""
import hashlib
import re
from pydantic import BaseModel, ConfigDict, Field
from app.math_tools.verifier import (VerifyResult, verify_derivative, verify_determinant_2x2,
    verify_equivalent, verify_integral, verify_lhopital_conditions)
from app.tutor.misconception import Mistake, MISTAKES, detect_mistake


class StepCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: str = Field(pattern="^step-v1$")
    message: str = Field(min_length=1, max_length=4096)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _candidate(text):
    value = re.split(r"(?:对所有实数(?:都)?成立|对吗|正确吗|是否正确|能否|是不是|[,，。；;？?\n])", text, maxsplit=1)[0].strip()
    return value or None


def _extract_integral_attempt(text):
    compact = text.replace(" ", "")
    match = re.search(r"(?:∫|\\int)([^=]+)dx=([^，。\n]+)", compact)
    return (match[1], _candidate(match[2])) if match and _candidate(match[2]) else None


def _extract_derivative_request(text):
    compact = text.replace(" ", "").replace("$", "")
    match = re.search(r"d\((.+?)\)/dx(?:=([^，。\n]+))?", compact)
    if not match: match = re.search(r"(?:d/dx|求导)([^=，。\n]+)(?:=([^，。\n]+))?", compact)
    if not match: return None
    expression = _candidate(match[1])
    return (expression, _candidate(match[2]) if match[2] else None) if expression else None


def _extract_determinant_attempt(text):
    # Keep numeric separators; removing all spaces destroys the matrix boundary.
    compact = text.replace("$", "")
    match = re.search(r"\|(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*;\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\|(?:\s*=\s*([^，。\n]+))?", compact)
    if not match: return None
    a,b,c,d = map(float, match.groups()[:4])
    return [[a,b],[c,d]], _candidate(match[5]) if match[5] else None


def _extract_equivalence_attempt(text):
    if "=" not in text or any(word in text for word in ("求解", "解方程")):
        return None
    for part in re.split(r"[,，;；\n]", text.replace("$", "")):
        part = re.sub(r"^(?:我算|我觉得|这一步|化简|展开|等价)[:：]?\s*", "", part.strip())
        if part.count("=") != 1: continue
        lhs, rhs = part.split("=")
        lhs, rhs = lhs.strip(), _candidate(rhs)
        if lhs and rhs and not re.search(r"[\u4e00-\u9fff]", lhs):
            return lhs, rhs
    return None


def _bind(result, message, candidate, *, origin=None):
    result.input_hash = digest(message)
    result.candidate_hash = digest(candidate) if candidate is not None else None
    result.origin = origin or ("student_claim" if candidate is not None else result.origin)
    if not result.scope_complete and result.execution_status == "succeeded" and "所有实数" in message and result.scope == "expression_equivalence":
        result.verified, result.is_correct = False, None
        result.unknown_reason = "claim_scope_mismatch"
        result.summary += " 本次范围不足以核对你的全域主张。"
    # Scoped checks with restrictions do not grade an unqualified whole-domain claim.
    result.eligible_learning_evidence = bool(
        result.origin == "student_claim" and candidate is not None and result.verified
        and result.is_correct is not None and result.scope_complete
        and not any(word in message for word in ("复数", "complex", "一般通解"))
    )
    return result


def _confirmed_mistake(result, expression, candidate):
    if not result.eligible_learning_evidence or result.is_correct is not False:
        return None
    from app.math_tools.safe_symbolic import normalize_math
    try:
        left, right = normalize_math(expression), normalize_math(candidate)
    except ValueError:
        return None
    if result.scope == "derivative" and left == "sin(x**2)" and right == "cos(x**2)":
        return MISTAKES["CHAIN_RULE_MISSING_INNER_DERIVATIVE"]
    if result.scope == "integral_candidate":
        match = re.fullmatch(r"x\*\*\(?([1-8])\)?", left)
        if match and right in (f"x**{int(match[1])+1}", f"x**({int(match[1])+1})"):
            return MISTAKES["POWER_INTEGRAL_MISSING_DIVISOR"]
    if result.scope == "determinant_2x2" and result.expected and result.actual:
        try:
            if float(result.expected) == -float(result.actual):
                return MISTAKES["DETERMINANT_SIGN_ERROR"]
        except ValueError:
            pass
    return None


def _single_claim_envelope(text, *, matrix=False):
    """Unknown surrounding givens cannot silently become a global-real verdict."""
    prefix = r"^(?:请帮我检查|帮我检查|请检查|检查一下|检查|我计算得到|我得到|我算|我觉得|这一步|求导|求|计算|核对|验算|化简|展开|等价|二阶行列式|不定积分)\s*[:：]?\s*"
    text = text.strip(" ,，;；\n")
    for _ in range(8):
        new = re.sub(prefix, "", text).strip(" ,，;；\n")
        if new == text: break
        text = new
    for _ in range(4):
        new = re.sub(r"[,，\s]*(?:对所有实数(?:都)?成立|对吗|正确吗|是否正确|请解释(?:一下)?(?:原因)?|请核对)[？?。\s]*$", "", text).strip(" ,，;；\n")
        if new == text: break
        text = new
    if matrix:
        text = re.sub(r"\|[^|]+\|", "x", text, count=1)
    if re.search(r"[\u4e00-\u9fff,，;；\n]", text): return False
    text = text.replace("d/dx", " ")
    names = re.findall(r"(?<![A-Za-z_0-9])[A-Za-z_][A-Za-z_0-9]*", text)
    return all(name in {"x", "pi", "e", "C", "d", "dx", "sin", "cos", "tan", "exp", "log", "ln", "sqrt", "Abs",
                        "frac", "left", "right", "cdot", "times"} for name in names)


def candidate_binding(message):
    """Cheap parent-side binding; no symbolic operation or normalization."""
    for extract, scope in ((_extract_integral_attempt, "integral_candidate"),
                           (_extract_derivative_request, "derivative"),
                           (_extract_determinant_attempt, "determinant_2x2")):
        found = extract(message)
        if found: return scope, found[1]
    if any(word in message.lower() for word in ("洛必达", "lhopital", "l'hopital")):
        return "indeterminate_form", None
    equivalent = _extract_equivalence_attempt(message)
    return ("expression_equivalence", equivalent[1]) if equivalent else ("none", None)


def check_step(message: str) -> tuple[VerifyResult, Mistake | None]:
    if not isinstance(message, str) or not 1 <= len(message) <= 4096:
        return VerifyResult(False, None, "输入超出本步核验预算。", execution_status="rejected", unknown_reason="message_budget"), None
    if "复数" in message or "complex" in message.lower():
        return _bind(VerifyResult(False, None, "本步只支持实数x，未核对复数域。", execution_status="rejected", unknown_reason="domain_not_supported"), message, None), None
    constraint_text = re.sub(r"(?:已知|设|假设)?\s*x\s*(?:为|是|∈)\s*(?:实数|R|ℝ)(?=$|[,，;；\s])", "", message)
    if (message.count("=") > 1 or any(word in constraint_text for word in ("假设", "已知", "当", "若", "设", "其中", "区间", "代入", "∈"))
            or any(sign in constraint_text.replace("->", "") for sign in ("<", ">", "≤", "≥", "!=", "≠"))):
        return _bind(VerifyResult(False, None, "本步含额外条件或多条等式，首版未绑定这些条件；请分开确认，不能忽略前提判对错。",
                                  execution_status="rejected", unknown_reason="additional_assumptions_not_supported"), message, None), None
    integral = _extract_integral_attempt(message)
    derivative = _extract_derivative_request(message)
    determinant = _extract_determinant_attempt(message)
    equivalent = _extract_equivalence_attempt(message)
    if (integral or derivative or determinant or equivalent) and not _single_claim_envelope(constraint_text, matrix=bool(determinant)):
        return _bind(VerifyResult(False, None, "本步还有未绑定的文字前提或多段内容；请分开确认条件和候选，不能按全实数范围判对错。",
                                  execution_status="rejected", unknown_reason="claim_context_not_bound"), message, None), None
    if integral:
        expression, candidate = integral
        result = _bind(verify_integral(expression, "x", candidate), message, candidate)
    elif derivative:
        expression, candidate = derivative
        result = _bind(verify_derivative(expression, "x", candidate), message, candidate)
    elif determinant:
        expression, candidate = determinant
        result = _bind(verify_determinant_2x2(expression, candidate), message, candidate)
        sign_error = (result.eligible_learning_evidence and result.is_correct is False
                      and float(result.actual) == expression[0][0]*expression[1][1] + expression[0][1]*expression[1][0])
        return result, MISTAKES["DETERMINANT_SIGN_ERROR"] if sign_error else None
    elif any(word in message.lower() for word in ("洛必达", "lhopital", "l'hopital")):
        return _bind(verify_lhopital_conditions(message), message, None), None
    else:
        if equivalent:
            expression, candidate = equivalent
            result = _bind(verify_equivalent(expression, candidate), message, candidate)
        else:
            clue = detect_mistake(message)
            result = VerifyResult(False, None, (f"待核对的教学线索：{clue.label}，尚无确定学生错误证据。" if clue else "未识别到受支持的学生候选，本轮未请求自动核验。"),
                                  origin="heuristic" if clue else "none", unknown_reason="heuristic_only" if clue else "")
            return _bind(result, message, None), None
    return result, _confirmed_mistake(result, expression, candidate) if candidate is not None else None
