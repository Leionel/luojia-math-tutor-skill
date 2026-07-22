"""Matplotlib 可视化服务。"""

import base64
import ast
import io
from enum import Enum

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

try:
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    pass


class VizType(str, Enum):
    FUNCTION_CURVE = "function_curve"
    INTEGRAL_AREA = "integral_area"
    PROBABILITY_DENSITY = "pdf"


ALLOWED_FUNCTIONS = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "log": np.log,
    "sqrt": np.sqrt,
    "abs": np.abs,
}

ALLOWED_CONSTANTS = {
    "pi": np.pi,
    "e": np.e,
}


class UnsafeExpressionError(ValueError):
    pass


def _safe_eval_expr(expr: str, x: np.ndarray) -> np.ndarray:
    if not isinstance(expr, str) or len(expr) > 200:
        raise UnsafeExpressionError("Expression is too long or invalid")

    parsed = ast.parse(expr.replace("^", "**"), mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id == "x":
                return x
            if node.id in ALLOWED_CONSTANTS:
                return ALLOWED_CONSTANTS[node.id]
            raise UnsafeExpressionError(f"Unsupported name: {node.id}")
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
            raise UnsafeExpressionError("Unsupported operator")
        if isinstance(node, ast.Call):
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "np"
            ):
                func_name = node.func.attr
            if func_name not in ALLOWED_FUNCTIONS:
                raise UnsafeExpressionError("Unsupported function")
            if node.keywords:
                raise UnsafeExpressionError("Keyword arguments are not supported")
            return ALLOWED_FUNCTIONS[func_name](*[evaluate(arg) for arg in node.args])
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "np"
            and node.attr in ALLOWED_CONSTANTS
        ):
            return ALLOWED_CONSTANTS[node.attr]
        raise UnsafeExpressionError("Unsupported expression")

    value = evaluate(parsed)
    y = np.asarray(value)
    if y.shape == ():
        y = np.full_like(x, float(y), dtype=float)
    if y.shape != x.shape:
        raise UnsafeExpressionError("Expression shape does not match x")
    return y.astype(float)


def generate_plot(viz_type: VizType, params: dict) -> str:
    """Generate a plot and return base64 PNG string."""
    fig, ax = plt.subplots(1, 1, figsize=(6, 4), dpi=100)

    if viz_type == VizType.FUNCTION_CURVE:
        _plot_function_curve(ax, params)
    elif viz_type == VizType.INTEGRAL_AREA:
        _plot_integral_area(ax, params)
    elif viz_type == VizType.PROBABILITY_DENSITY:
        _plot_pdf(ax, params)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def _plot_function_curve(ax, params: dict):
    expr_str = params.get("expr", "x**2")
    x_min = params.get("x_min", -5)
    x_max = params.get("x_max", 5)
    title = params.get("title", f"y = {expr_str}")

    x = np.linspace(x_min, x_max, 400)
    try:
        y = _safe_eval_expr(expr_str, x)
    except Exception:
        y = x ** 2

    ax.plot(x, y, "b-", linewidth=2, label=f"y = {expr_str}")
    ax.axhline(y=0, color="k", linewidth=0.5)
    ax.axvline(x=0, color="k", linewidth=0.5)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(title)


def _plot_integral_area(ax, params: dict):
    expr_str = params.get("expr", "x**2")
    a = params.get("a", 0)
    b = params.get("b", 2)

    x = np.linspace(a - 1, b + 1, 400)
    try:
        y = _safe_eval_expr(expr_str, x)
    except Exception:
        y = x ** 2

    ax.plot(x, y, "b-", linewidth=2, label=f"y = {expr_str}")
    x_fill = np.linspace(a, b, 200)
    try:
        y_fill = _safe_eval_expr(expr_str, x_fill)
    except Exception:
        y_fill = x_fill ** 2
    ax.fill_between(x_fill, y_fill, alpha=0.3, color="blue", label=f"Area [{a}, {b}]")
    ax.axhline(y=0, color="k", linewidth=0.5)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"Integral of {expr_str} from {a} to {b}")


def _plot_pdf(ax, params: dict):
    dist = params.get("dist", "normal")
    mu = params.get("mu", 0)
    sigma = params.get("sigma", 1)

    x = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 400)
    y = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

    ax.plot(x, y, "b-", linewidth=2, label=f"N({mu}, {sigma}^2)")
    ax.fill_between(x, y, alpha=0.2, color="blue")
    ax.axvline(x=mu, color="r", linestyle="--", alpha=0.5, label=f"mean={mu}")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    ax.set_title(f"PDF: Normal({mu}, {sigma}^2)")
