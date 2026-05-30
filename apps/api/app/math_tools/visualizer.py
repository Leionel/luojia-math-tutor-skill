"""Matplotlib 可视化服务。"""

import io
import base64
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
        y = eval(expr_str, {"x": x, "np": np, "sin": np.sin, "cos": np.cos,
                            "exp": np.exp, "log": np.log, "sqrt": np.sqrt,
                            "pi": np.pi, "abs": np.abs, "tan": np.tan})
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
        y = eval(expr_str, {"x": x, "np": np, "sin": np.sin, "cos": np.cos,
                            "exp": np.exp, "log": np.log, "sqrt": np.sqrt})
    except Exception:
        y = x ** 2

    ax.plot(x, y, "b-", linewidth=2, label=f"y = {expr_str}")
    x_fill = np.linspace(a, b, 200)
    try:
        y_fill = eval(expr_str, {"x": x_fill, "np": np, "sin": np.sin, "cos": np.cos,
                                  "exp": np.exp, "log": np.log, "sqrt": np.sqrt})
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
