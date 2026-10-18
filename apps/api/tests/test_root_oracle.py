import math
from decimal import Decimal, localcontext
import pytest
from app.math_tools.root_expression import RootExpression, Interval, ExpressionError
from app.math_tools.root_finding import RootAttempt, diagnose


def report(**kwargs):
    return diagnose(RootAttempt(**kwargs))


@pytest.mark.parametrize("expression", ["__import__('os')", "x.__class__", "x[0]", "[x]", "sum(x)", "2**9999", "x**x", "lambda:1"])
def test_expression_rejects_code_and_unbounded_work(expression):
    with pytest.raises(ExpressionError): RootExpression(expression)


def test_analytic_derivative_and_interval_reference():
    expr = RootExpression("x^3-2*x+2")
    for x in [-2, -1, 0, 1, 2]:
        assert expr.evaluate(x, derivative=True) == pytest.approx(3*x*x-2)
    for formula in ["x^2-2", "sin(x)", "cos(x)", "1/(x+3)", "exp(x)", "log(x+3)"]:
        expr = RootExpression(formula)
        bound = expr.evaluate(Interval(-1, 1))
        for k in range(101):
            assert bound.lo <= expr.evaluate(-1 + k/50) <= bound.hi
    with pytest.raises(ExpressionError): RootExpression("1/x").evaluate(Interval(-1,1))


@pytest.mark.parametrize("data,family,status", [
 ({"method":"newton","function":"x^2-2","iterates":[1,3]}, "newton_formula", "contradicted"),
 ({"method":"newton","function":"x^2-2","derivative":"x","iterates":[1,1.5]}, "newton_formula", "contradicted"),
 ({"method":"newton","function":"x^3-2*x+2","iterates":[1,0,1]}, "newton_cycle", "contradicted"),
 ({"method":"newton","function":"x^2-2","iterates":[0,1]}, "newton_derivative_zero", "contradicted"),
 ({"method":"newton","function":"x^2-2","variant":"damped","damping":1e-8,"iterates":[1,1.000000005],"stop_reason":"step"}, "newton_stop_step", "contradicted"),
 ({"method":"newton","function":"0.00000001*(x-10)","iterates":[0],"stop_reason":"residual"}, "residual_without_error_bound", "inconclusive"),
 ({"method":"bisection","function":"x^2-2","brackets":[[2,3]]}, "bisection_bracket", "contradicted"),
 ({"method":"bisection","function":"x^2-2","brackets":[[1,2],[1.5,2]]}, "bisection_update", "contradicted"),
 ({"method":"bisection","function":"x^2-2","brackets":[[1,2]],"stop_reason":"bracket"}, "bisection_stop", "contradicted"),
 ({"method":"fixed_point","function":"x^2-2","phi":"(x+2/x)/2","iterates":[1,1.25]}, "fixed_point_update", "contradicted"),
 ({"method":"fixed_point","function":"x","phi":"2*x","iterates":[0.1,0.2,0.4]}, "fixed_point_conditions", "inconclusive"),
 ({"method":"newton","function":"x^2-2","iterates":[1,"NaN"]}, "numeric_nonfinite", "contradicted"),
 ({"method":"newton","function":"x^2-2","iterates":[1,1.5],"stop_reason":"iteration_limit"}, "iteration_limit", "inconclusive"),
])
def test_error_families(data, family, status):
    result = report(**data)
    assert (result["family"], result["status"], result["complete"]) == (family,status,False)
    assert result["next_probe"]


def test_newton_root_error_against_independent_decimal_reference():
    with localcontext() as context:
        context.prec = 50
        root = Decimal(2).sqrt()
    xs = [1.0]
    for _ in range(5): xs.append((xs[-1] + 2 / xs[-1])/2)
    result = report(method="newton",function="x^2-2",iterates=xs,interval=[1,2])
    assert result["status"] == "supported" and result["complete"]
    assert abs(Decimal(str(xs[-1])) - root) <= Decimal(str(result["evidence"]["error_bound"])) + Decimal("1e-15")


@pytest.mark.parametrize("data", [
 {"method":"newton","function":"x^2-2","variant":"damped","damping":0.5,"iterates":[1,1.25]},
 {"method":"newton","function":"(x-1)^2","variant":"modified","multiplicity":2,"iterates":[2,1],"goal":"residual"},
 {"method":"bisection","function":"x^2-4","iterates":[2],"brackets":[[2,3]]},
 {"method":"bisection","function":"x^2-2","iterates":[math.sqrt(2)],"brackets":[[1,2]],"goal":"residual"},
 {"method":"fixed_point","function":"x-0.5","phi":"0.5","iterates":[0,0.5],"interval":[0,1],"goal":"residual"},
])
def test_legal_alternatives_are_not_rejected(data):
    result = report(**data)
    assert result["status"] == "supported", result


def test_no_false_success_from_discontinuous_sign_change_or_unrelated_fixed_point():
    assert not report(method="bisection",function="1/x",brackets=[[-1,1]])["complete"]
    result = report(method="fixed_point",function="0.00000001*(x-10)",phi="0",iterates=[1,0,0],interval=[-1,1])
    assert result["status"] == "inconclusive" and not result["complete"]


def test_missing_conditions_and_tool_failure_are_unknown(monkeypatch):
    assert report(method="newton",function="x^2-2")["status"] == "inconclusive"
    monkeypatch.setattr(RootExpression, "evaluate", lambda *args,**kwargs: (_ for _ in ()).throw(RuntimeError("offline failure")))
    assert report(method="newton",function="x^2-2",iterates=[1])["status"] == "tool_error"


@pytest.mark.parametrize("tail", [-1, "NaN"])
def test_first_wrong_update_precedes_later_invalid_observation(tail):
    # Independently: Newton for sqrt(x)-2 maps x to 4*sqrt(x)-x.
    # 1 -> 3 is right; 3 -> 4 is wrong, before the invalid x3.
    expected = 4 * math.sqrt(3) - 3
    assert not math.isclose(expected, 4, abs_tol=1e-8)
    result = report(method="newton", function="sqrt(x)-2", initial_value=1,
                    iterates=[1, 3, 4, tail], goal="residual", stop_reason="iteration_limit")
    assert result["family"] == "newton_formula" and result["error_step"] == 2
    assert result["evidence"]["reference_step"] == pytest.approx(expected)
    assert all(row["stop_reason"] == "none" for row in result["trace"])
    # A valid prefix must not cause a later domain error to disappear.
    correct_prefix = report(method="newton", function="sqrt(x)-2", initial_value=1,
                            iterates=[1, 3, expected, tail], goal="residual")
    assert correct_prefix["family"] == "numeric_nonfinite" and correct_prefix["error_step"] == 3
    assert not correct_prefix["complete"]


def test_fixed_point_first_update_error_and_initial_value_precede_bad_tail():
    result = report(method="fixed_point", function="sqrt(x)-2", phi="(x+4)/2",
                    initial_value=0, iterates=[0, 2, 4, -1], goal="residual")
    assert result["family"] == "fixed_point_update" and result["error_step"] == 2
    assert result["evidence"]["reference_step"] == 3  # g(2)=(2+4)/2
    initial = report(method="newton", function="sqrt(x)-2", initial_value=2,
                     iterates=[1, 3, 4, -1])
    assert initial["family"] == "initial_value" and initial["error_step"] == 0
