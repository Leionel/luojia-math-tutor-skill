"""Finite mathematical syntax -> explicit SymPy constructors, never string eval.

Application requests run the expensive operations in the owned fixed worker.
The native tool grammar stays separate and retains its existing allowlist.
"""
import ast
import io
import math
import re
import tokenize


class MathSyntaxError(ValueError):
    pass


FUNCTIONS = {"sin", "cos", "tan", "exp", "log", "sqrt", "Abs"}


def normalize_math(source: str) -> str:
    if not isinstance(source, str) or not 1 <= len(source) <= 512:
        raise MathSyntaxError("expression_budget")
    text = source.strip().replace("$", "").replace("π", "pi")
    for old, new in {r"\left": "", r"\right": "", r"\cdot": "*", r"\times": "*",
                     r"\pi": "pi", r"\sin": "sin", r"\cos": "cos", r"\tan": "tan",
                     r"\ln": "log", r"\sqrt": "sqrt"}.items():
        text = text.replace(old, new)
    digits = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
    text = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+", lambda m: "^(" + m[0].translate(digits) + ")", text)
    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"((\1)/(\2))", text)
    text = text.replace("{", "(").replace("}", ")").replace("^", "**")
    text = re.sub(r"\b(sin|cos|tan)\s*x\b", r"\1(x)", text)
    if text.count("|") == 2:
        text = re.sub(r"\|([^|]+)\|", r"Abs(\1)", text)
    try:
        tokens = [t for t in tokenize.generate_tokens(io.StringIO(text).readline)
                  if t.type not in {tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL}]
    except (tokenize.TokenError, IndentationError) as exc:
        raise MathSyntaxError("expression_rejected") from exc
    out = []
    previous = None
    for token in tokens:
        if token.type not in {tokenize.NAME, tokenize.NUMBER, tokenize.OP}:
            raise MathSyntaxError("expression_rejected")
        if token.type == tokenize.OP and token.string not in {"+", "-", "*", "/", "**", "(", ")"}:
            raise MathSyntaxError("expression_rejected")
        if previous:
            left = previous.type in {tokenize.NAME, tokenize.NUMBER} or previous.string == ")"
            right = token.type in {tokenize.NAME, tokenize.NUMBER} or token.string == "("
            function_call = previous.string in FUNCTIONS and token.string == "("
            if left and right and not function_call:
                out.append("*")
        out.append(token.string)
        previous = token
    normalized = "".join(out)
    if not normalized or len(normalized) > 2048:
        raise MathSyntaxError("expression_budget")
    return normalized


def math_tree(source: str, *, allow_constant=False):
    try:
        tree = ast.parse(normalize_math(source), mode="eval")
    except (SyntaxError, RecursionError) as exc:
        raise MathSyntaxError("expression_rejected") from exc
    validate_tree(tree, allow_constant=allow_constant)
    return tree


def exponent_value(node):
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        sign = -1 if isinstance(node.op, ast.USub) else 1
        node = node.operand
    if isinstance(node, ast.Constant) and type(node.value) is int and -8 <= sign * node.value <= 8:
        return sign * node.value
    if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
            and isinstance(node.left, ast.Constant) and type(node.left.value) is int and node.left.value == 1
            and isinstance(node.right, ast.Constant) and type(node.right.value) is int and node.right.value == 2
            and sign == 1):
        return 0.5
    raise MathSyntaxError("power_not_supported")


def validate_tree(tree, *, allow_constant=False):
    if len(list(ast.walk(tree))) > 64:
        raise MathSyntaxError("expression_budget")
    names = {"x", "pi", "e"} | ({"C"} if allow_constant else set())
    def check(node, depth=0):
        if depth > 12:
            raise MathSyntaxError("expression_budget")
        if isinstance(node, ast.Expression):
            return check(node.body, depth + 1)
        if isinstance(node, ast.Name) and node.id in names:
            return 1
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            if abs(node.value) > 1e12 or not math.isfinite(node.value):
                raise MathSyntaxError("number_budget")
            return 1
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return check(node.operand, depth + 1)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS and len(node.args) == 1 and not node.keywords:
            return check(node.args[0], depth + 1)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            if isinstance(node.op, ast.Pow):
                if isinstance(node.left, ast.Name) and node.left.id == "e":
                    return check(node.right, depth + 1)
                cost = check(node.left, depth + 1) * max(1, abs(exponent_value(node.right)))
            else:
                cost = check(node.left, depth + 1) + check(node.right, depth + 1)
            if cost > 32:
                raise MathSyntaxError("expression_budget")
            return cost
        raise MathSyntaxError("expression_rejected")
    check(tree)


def construct_math(tree, *, allow_constant=False, derivative=False):
    """Return expression and preserved sufficient domain/differentiability conditions."""
    import sympy as sp
    validate_tree(tree, allow_constant=allow_constant)
    x = sp.Symbol("x", real=True)
    conditions = []
    def require(condition):
        simplified = sp.simplify(condition)
        if simplified is sp.false:
            raise MathSyntaxError("empty_real_domain")
        if simplified is not sp.true and simplified not in conditions:
            conditions.append(simplified)
    def build(node):
        if isinstance(node, ast.Constant):
            return sp.Rational(str(node.value))
        if isinstance(node, ast.Name):
            return {"x": x, "pi": sp.pi, "e": sp.E, "C": sp.Symbol("C", real=True)}[node.id]
        if isinstance(node, ast.UnaryOp):
            value = build(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.Call):
            value = build(node.args[0])
            name = node.func.id
            if name == "log": require(sp.Gt(value, 0))
            if name == "sqrt": require(sp.Gt(value, 0) if derivative and x in value.free_symbols else sp.Ge(value, 0))
            if name == "tan": require(sp.Ne(sp.cos(value), 0))
            if name == "Abs" and derivative and x in value.free_symbols: require(sp.Ne(value, 0))
            return {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "exp": sp.exp,
                    "log": sp.log, "sqrt": sp.sqrt, "Abs": sp.Abs}[name](value)
        left = build(node.left)
        if isinstance(node.op, ast.Pow):
            if isinstance(node.left, ast.Name) and node.left.id == "e":
                return sp.exp(build(node.right))
            exponent = exponent_value(node.right)
            if exponent < 0: require(sp.Ne(left, 0))
            if exponent == 0.5:
                require(sp.Gt(left, 0) if derivative and x in left.free_symbols else sp.Ge(left, 0))
                return sp.sqrt(left)
            return left ** int(exponent)
        right = build(node.right)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        require(sp.Ne(right, 0))
        return left / right
    value = build(tree.body)
    if value.has(sp.zoo, sp.nan, sp.oo, -sp.oo) or len(str(value)) > 8192:
        raise MathSyntaxError("non_finite_expression")
    return value, conditions


def parse_bounded(source, *, allow_constant=False, derivative=False):
    return construct_math(math_tree(source, allow_constant=allow_constant),
                          allow_constant=allow_constant, derivative=derivative)
