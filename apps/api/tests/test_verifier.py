from app.math_tools.verifier import (
    compute_matrix_product,
    verify_derivative,
    verify_determinant_2x2,
    verify_integral,
    verify_lhopital_conditions,
)


def test_integral_candidate_correct():
    result = verify_integral("x^2", "x", "x^3/3 + C")
    assert result.verified
    assert result.is_correct is True


def test_integral_candidate_wrong():
    result = verify_integral("x^2", "x", "x^3")
    assert result.verified
    assert result.is_correct is False
    assert "3*x**2" in result.summary


def test_chain_rule_derivative():
    result = verify_derivative("sin(x^2)", "x", "2*x*cos(x^2)")
    assert result.verified
    assert result.is_correct is True


def test_matrix_product():
    result = compute_matrix_product([[1, 2]], [[3], [4]])
    assert result.execution_status == "succeeded"
    assert result.is_correct is None
    assert result.origin == "system_calculation"
    assert "[[11]]" in result.actual


def test_determinant_2x2_correct():
    result = verify_determinant_2x2([[1, 2], [3, 4]], "-2")
    assert result.verified
    assert result.is_correct is True


def test_determinant_2x2_wrong():
    result = verify_determinant_2x2([[1, 2], [3, 4]], "10")
    assert result.verified
    assert result.is_correct is False
    assert "-2" in result.summary


def test_lhopital_checks_form_without_certifying_theorem():
    result = verify_lhopital_conditions("lim x->0 sinx/x 能直接用洛必达吗？")
    assert result.verified
    assert result.is_correct is None
    assert result.actual == "0/0"
    assert result.scope == "indeterminate_form"


def test_lhopital_condition_unsatisfied():
    result = verify_lhopital_conditions("这个极限能直接用洛必达吗：lim x->1 x/x")
    assert result.verified
    assert result.is_correct is False

