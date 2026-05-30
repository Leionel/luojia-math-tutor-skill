from app.math_tools.step_checker import check_step
from app.tutor.misconception import detect_mistake


def test_step_checker_detects_power_integral_missing_divisor():
    result, mistake = check_step("我算 ∫ x^2 dx = x^3，对吗？")
    assert result.verified
    assert result.is_correct is False
    assert mistake is not None
    assert mistake.code == "POWER_INTEGRAL_MISSING_DIVISOR"


def test_detects_missing_integration_constant():
    mistake = detect_mistake("不定积分 ∫ x dx = x^2/2")
    assert mistake is not None
    assert mistake.code == "MISSING_INTEGRATION_CONSTANT"


def test_detects_conditional_probability_denominator_issue():
    mistake = detect_mistake("条件概率这里是不是分母应该用 P(A)？")
    assert mistake is not None
    assert mistake.code == "CONDITIONAL_PROBABILITY_DENOMINATOR_ERROR"


def test_detects_independence_confusion():
    mistake = detect_mistake("A、B 互斥是不是就独立？")
    assert mistake is not None
    assert mistake.code == "INDEPENDENCE_CONFUSION"


def test_detects_chain_rule_missing_inner():
    result, mistake = check_step("求 d/dx sin(x^2) = cos(x^2)")
    assert result.verified
    assert result.is_correct is False
    assert mistake is not None
    assert mistake.code == "CHAIN_RULE_MISSING_INNER_DERIVATIVE"


def test_detects_lhopital_without_indeterminate():
    result, mistake = check_step("这个极限能直接用洛必达吗：lim x->1 x/x")
    assert result.verified
    assert result.is_correct is False
    assert mistake is not None
    assert mistake.code == "LHOPITAL_WITHOUT_INDETERMINATE_FORM"


def test_detects_determinant_sign_error():
    result, mistake = check_step("计算二阶行列式 |1 2; 3 4| = 10")
    assert result.verified
    assert result.is_correct is False
    assert mistake is not None
    assert mistake.code == "DETERMINANT_SIGN_ERROR"

