"""Fixed entry point: reads a bounded task, never Python source."""
import ast
import json
from pathlib import Path
import sys
import site

# -I ignores external PYTHONPATH; only this repository's fixed app is imported.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
# -I omits the user site used by this Windows interpreter's installed packages.
# Add that fixed directory without processing .pth files or PYTHONPATH.
sys.path.append(site.getusersitepackages())
from app.agents.typed_tools import MAX_INPUT, validate_call, ToolCall, expression_tree


def differentiate(expression):
    import sympy as sp
    x = sp.Symbol("x", real=True)
    def construct(node):
        if isinstance(node, ast.Constant):
            return sp.Rational(str(node.value))
        if isinstance(node, ast.Name):
            return {"x": x, "pi": sp.pi, "e": sp.E}[node.id]
        if isinstance(node, ast.UnaryOp):
            return -construct(node.operand) if isinstance(node.op, ast.USub) else construct(node.operand)
        if isinstance(node, ast.Call):
            return {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "exp": sp.exp, "log": sp.log, "sqrt": sp.sqrt}[node.func.id](construct(node.args[0]))
        left, right = construct(node.left), construct(node.right)
        if isinstance(node.op, ast.Add): return left+right
        if isinstance(node.op, ast.Sub): return left-right
        if isinstance(node.op, ast.Mult): return left*right
        if isinstance(node.op, ast.Div): return left/right
        return left**right
    value = construct(expression_tree(expression).body)
    derivative = str(sp.diff(value, x))
    if len(derivative.encode()) > 8192 or value.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
        raise ValueError("symbolic_budget")
    return {"derivative": derivative, "variable": "x", "evidence_scope": "symbolic_derivative",
            "assumptions": ["x为实数，仅在原表达式有定义且可微的区域适用；未求解定义域。",
                            "log要求正实参数，sqrt在求导处要求正实参数；分母和tan极点需另核对。"],
            "whole_answer_verified": False}


def main():
    try:
        packet = sys.stdin.buffer.read(MAX_INPUT+1)
        if len(packet) > MAX_INPUT: raise ValueError("input_budget")
        data = json.loads(packet)
        if set(data) != {"name", "arguments"}: raise ValueError("fields")
        if data["name"] == "student_step_check":
            from dataclasses import asdict
            from app.math_tools.step_checker import StepCheckRequest, check_step
            request = StepCheckRequest.model_validate(data["arguments"], strict=True)
            verification, mistake = check_step(request.message)
            print(json.dumps({"verification": asdict(verification), "mistake_code": mistake.code if mistake else None},
                             ensure_ascii=True, allow_nan=False))
            return
        call = ToolCall(call_id="worker", **data)
        args = validate_call(call)
        if call.name == "math_differentiate":
            result = differentiate(args["expression"])
        else:
            from pydantic import TypeAdapter
            from app.math_tools.numerical_lab import NumericalTask, run_numerical
            result = run_numerical(TypeAdapter(NumericalTask).validate_python(args["task"], strict=True))
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    except Exception:
        print(json.dumps({"error_code": "tool_parameters_invalid"}))


if __name__ == "__main__":
    main()
