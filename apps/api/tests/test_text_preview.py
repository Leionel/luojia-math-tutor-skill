"""Display truncation must never produce unrenderable LaTeX."""

import re

from app.text_preview import truncate_text

MATH = "设 $x^{*}$ 为单根，则 $|x_{k+1} - x^{*}| \\leq \\frac{L}{d} |x_{k}|^{2}$ 成立。"


def test_short_text_is_returned_unchanged() -> None:
    assert truncate_text("定义 1.1 不动点", 80) == "定义 1.1 不动点"


def test_long_text_is_truncated_with_an_ellipsis() -> None:
    text = "数值分析关注算法的收敛性与误差传播。" * 20

    result = truncate_text(text, 40)

    assert result.endswith("…")
    assert len(result) <= 40 + len("…")


def test_zero_or_negative_limit_yields_empty() -> None:
    assert truncate_text("abc", 0) == ""
    assert truncate_text("abc", -5) == ""


def test_does_not_cut_inside_an_inline_math_span() -> None:
    result = truncate_text(MATH, 40)

    assert result.count("$") % 2 == 0, f"unbalanced math span: {result!r}"


def test_does_not_cut_inside_a_display_math_span() -> None:
    text = "前置说明文字，用于把长度推过限制。$$ |e_{k+1}| \\leq C |e_k|^2 $$ 后置文字。"

    result = truncate_text(text, 34)

    assert result.count("$$") % 2 == 0, f"unbalanced display math: {result!r}"


def test_does_not_leave_an_unbalanced_brace() -> None:
    text = "误差估计为 " + "\\frac{L}{d}" * 12

    result = truncate_text(text, 45)

    assert result.count("{") == result.count("}"), f"unbalanced braces: {result!r}"


def test_does_not_end_on_a_partial_or_argumentless_command() -> None:
    text = "收敛速度分析 " + "\\operatorname " * 8

    result = truncate_text(text, 30).rstrip("…")

    assert not re.search(r"\\[A-Za-z]*$", result), f"dangling command: {result!r}"


def test_prefers_a_paragraph_boundary() -> None:
    text = (
        "第一段完整的内容，长度足够触发截断行为。\n\n"
        "第二段的内容明显更长，因此整体长度一定会超过限制，不应该出现在结果里面。"
    )

    result = truncate_text(text, 40)

    assert "第二段" not in result
    assert result.startswith("第一段")


def test_real_theorem_proof_conclusion_survives_truncation() -> None:
    """The regression this module exists for: a cut mid-`\frac{`."""
    text = (
        "## 定理 2.4 (Newton 法的局部二次收敛性)\n\n"
        "令 $x^{*}$ 为 f(x) 的单根，f 在邻域内二次连续可微，则 Newton 法产生的序列至少二次收敛。\n\n"
        "证明 由泰勒展开可得 $x_{k+1} - x^{*} + \\frac{f(x^{*}) - f(x_k)}{f'(x_k)}$，"
        "整理后得到误差递推关系。\n\n"
        "于是 $|x_{k+1} - x^{*}| \\leq \\frac{L}{d} |x^{*} - x_k|^2$，二次收敛性得证。"
    )

    result = truncate_text(text, 240)

    assert result.count("$") % 2 == 0
    assert result.count("{") == result.count("}")
    assert "\\frac{" not in result or result.count("{") == result.count("}")
