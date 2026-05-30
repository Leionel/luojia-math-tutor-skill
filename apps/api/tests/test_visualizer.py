"""可视化服务测试。"""
import pytest
from app.math_tools.visualizer import VizType, generate_plot


class TestVisualizerFunctionCurve:
    def test_generates_base64_png(self):
        result = generate_plot(VizType.FUNCTION_CURVE, {"expr": "x**2", "x_min": -3, "x_max": 3})
        assert isinstance(result, str)
        assert len(result) > 100  # base64 string should be substantial

    def test_generates_with_trig(self):
        result = generate_plot(VizType.FUNCTION_CURVE, {"expr": "sin(x)", "x_min": -6, "x_max": 6})
        assert len(result) > 100


class TestVisualizerIntegralArea:
    def test_integral_area(self):
        result = generate_plot(VizType.INTEGRAL_AREA, {"expr": "x**2", "a": 0, "b": 2})
        assert len(result) > 100


class TestVisualizerPDF:
    def test_normal_pdf(self):
        result = generate_plot(VizType.PROBABILITY_DENSITY, {"mu": 0, "sigma": 1})
        assert len(result) > 100

    def test_custom_params(self):
        result = generate_plot(VizType.PROBABILITY_DENSITY, {"mu": 5, "sigma": 2})
        assert len(result) > 100
