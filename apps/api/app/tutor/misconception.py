import re
from dataclasses import dataclass


@dataclass
class Mistake:
    code: str
    label: str
    concept: str
    subject: str


MISTAKES = {
    "POWER_INTEGRAL_MISSING_DIVISOR": Mistake("POWER_INTEGRAL_MISSING_DIVISOR", "幂函数积分漏除以 n+1", "幂函数积分", "calculus"),
    "MISSING_INTEGRATION_CONSTANT": Mistake("MISSING_INTEGRATION_CONSTANT", "不定积分漏写常数 C", "不定积分", "calculus"),
    "CHAIN_RULE_MISSING_INNER_DERIVATIVE": Mistake("CHAIN_RULE_MISSING_INNER_DERIVATIVE", "链式法则漏乘内层导数", "链式法则", "calculus"),
    "LHOPITAL_WITHOUT_INDETERMINATE_FORM": Mistake("LHOPITAL_WITHOUT_INDETERMINATE_FORM", "未确认未定式就使用洛必达", "洛必达法则", "calculus"),
    "DETERMINANT_SIGN_ERROR": Mistake("DETERMINANT_SIGN_ERROR", "二阶行列式主副对角线符号错误", "二阶行列式", "linear_algebra"),
    "MATRIX_MULTIPLICATION_RULE_ERROR": Mistake("MATRIX_MULTIPLICATION_RULE_ERROR", "矩阵乘法行列配对错误", "矩阵乘法", "linear_algebra"),
    "EIGENVECTOR_NOT_SUBSTITUTED": Mistake("EIGENVECTOR_NOT_SUBSTITUTED", "特征向量未代回验证", "特征值与特征向量", "linear_algebra"),
    "INDEPENDENCE_CONFUSION": Mistake("INDEPENDENCE_CONFUSION", "混淆独立与互斥", "事件独立性", "probability"),
    "PDF_NOT_NORMALIZED": Mistake("PDF_NOT_NORMALIZED", "密度函数未归一化", "概率密度函数", "probability"),
    "CONDITIONAL_PROBABILITY_DENOMINATOR_ERROR": Mistake("CONDITIONAL_PROBABILITY_DENOMINATOR_ERROR", "条件概率分母错误", "条件概率", "probability"),
    "SIGN_ERROR": Mistake("SIGN_ERROR", "符号错误", "代数运算", "general"),
    "ALGEBRA_EXPANSION_ERROR": Mistake("ALGEBRA_EXPANSION_ERROR", "代数展开错误", "代数运算", "general"),
}


def detect_mistake(message: str, verifier_summary: str = "") -> Mistake | None:
    text = f"{message}\n{verifier_summary}"
    # Normalize Unicode superscripts for pattern matching
    superscript_map = {
        "¹": "^1", "²": "^2", "³": "^3",
        "⁴": "^4", "⁵": "^5", "⁶": "^6",
        "⁷": "^7", "⁸": "^8", "⁹": "^9", "⁰": "^0",
        "⁻": "^-",
    }
    for uni, replacement in superscript_map.items():
        text = text.replace(uni, replacement)
    compact = text.replace(" ", "")
    # Power integral missing divisor: verifier confirmed wrong + integrand is power of x
    if "∫" in text and verifier_summary and "不通过" in verifier_summary and "积分" in verifier_summary:
        if re.search(r"x\^\d", compact):
            return MISTAKES["POWER_INTEGRAL_MISSING_DIVISOR"]
    if "∫" in text and "x^2" in compact and "x^3" in compact and "/3" not in compact:
        return MISTAKES["POWER_INTEGRAL_MISSING_DIVISOR"]
    if "∫" in text and "+C" not in compact and "不定积分" in text:
        return MISTAKES["MISSING_INTEGRATION_CONSTANT"]
    if "sin(x^2)" in compact and ("cos(x^2)" in compact and "2x" not in compact):
        return MISTAKES["CHAIN_RULE_MISSING_INNER_DERIVATIVE"]
    if "洛必达" in text:
        has_indeterminate = any(key in text for key in ["0/0", "∞/∞", "无穷/无穷", "未定式"])
        if not has_indeterminate:
            if "条件" in text or "能直接" in text or "直接用" in text or "吗" in text:
                return MISTAKES["LHOPITAL_WITHOUT_INDETERMINATE_FORM"]
            if "lim" in compact and not any(key in compact for key in ["sinx/x", "sin(x)/x", "0/0"]):
                return MISTAKES["LHOPITAL_WITHOUT_INDETERMINATE_FORM"]
        if "未确认未定式" in verifier_summary:
            return MISTAKES["LHOPITAL_WITHOUT_INDETERMINATE_FORM"]
    if "互斥" in text and "独立" in text:
        return MISTAKES["INDEPENDENCE_CONFUSION"]
    if "条件概率" in text and ("分母" in text or "P(A)" in text or "P(B)" in text):
        return MISTAKES["CONDITIONAL_PROBABILITY_DENOMINATOR_ERROR"]
    if "密度" in text and ("积分为1" in text or "归一" in text):
        return MISTAKES["PDF_NOT_NORMALIZED"]
    if "行列式" in text and any(key in text for key in ["符号", "主对角线", "副对角线"]):
        return MISTAKES["DETERMINANT_SIGN_ERROR"]
    if "矩阵" in text and "乘" in text:
        return MISTAKES["MATRIX_MULTIPLICATION_RULE_ERROR"]
    if "特征" in text and "代回" in text:
        return MISTAKES["EIGENVECTOR_NOT_SUBSTITUTED"]
    if "行列式" in text and "=" in text:
        parts = text.split("=")
        if len(parts) >= 2:
            rhs = parts[-1].strip()
            try:
                val = float(rhs)
                if val != 0 and any(key in text for key in ["1 2", "12", "3 4", "34"]):
                    if abs(val - (-2)) > 1e-9:
                        return MISTAKES["DETERMINANT_SIGN_ERROR"]
            except Exception:
                pass
    return None

