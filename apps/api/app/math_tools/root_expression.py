"""Bounded arithmetic AST, analytic derivatives and conservative interval bounds.

No eval, SymPy parsing, student Python, filesystem or network capabilities.
Interval bounds are used as sufficient conditions, never sampled proof claims.
"""
import ast
import math
from dataclasses import dataclass


class ExpressionError(ValueError):
    pass


@dataclass(frozen=True)
class Interval:
    lo: float
    hi: float

    def __post_init__(self):
        if not math.isfinite(self.lo) or not math.isfinite(self.hi) or self.lo > self.hi:
            raise ExpressionError("无效或非有限区间")

    def __add__(self, other):
        other = interval(other)
        return outward(self.lo + other.lo, self.hi + other.hi)

    __radd__ = __add__

    def __neg__(self):
        return Interval(-self.hi, -self.lo)

    def __sub__(self, other):
        return self + -interval(other)

    def __rsub__(self, other):
        return interval(other) + -self

    def __mul__(self, other):
        other = interval(other)
        vals = [a * b for a in (self.lo, self.hi) for b in (other.lo, other.hi)]
        return outward(min(vals), max(vals))

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = interval(other)
        if other.lo <= 0 <= other.hi:
            raise ExpressionError("区间包含分母零点，不能保证连续性")
        return self * outward(1 / other.hi, 1 / other.lo)

    def __rtruediv__(self, other):
        return interval(other) / self

    def __pow__(self, power):
        if not isinstance(power, (int, float)) or int(power) != power or abs(power) > 32:
            raise ExpressionError("幂仅允许 -16 至 16 的整数")
        n = int(power)
        if n < 0:
            return interval(1) / (self ** -n)
        if n == 0:
            return interval(1)
        vals = [self.lo ** n, self.hi ** n]
        lo = 0 if n % 2 == 0 and self.lo <= 0 <= self.hi else min(vals)
        return outward(lo, max(vals))


def interval(value):
    return value if isinstance(value, Interval) else Interval(float(value), float(value))


def outward(lo, hi):
    return Interval(math.nextafter(lo, -math.inf), math.nextafter(hi, math.inf))


def unary(name, value):
    if not isinstance(value, Interval):
        return {"sin": math.sin, "cos": math.cos, "tan": math.tan,
                "exp": math.exp, "log": math.log, "sqrt": math.sqrt, "abs": abs}[name](value)
    a, b = value.lo, value.hi
    if name == "abs":
        return outward(0 if a <= 0 <= b else min(abs(a), abs(b)), max(abs(a), abs(b)))
    if name in ("sin", "cos"):
        if b - a >= 2 * math.pi:
            return Interval(-1, 1)
        offset = math.pi / 2 if name == "sin" else 0
        func = math.sin if name == "sin" else math.cos
        vals = [func(a), func(b)]
        for k in range(math.ceil((a - offset) / math.pi), math.floor((b - offset) / math.pi) + 1):
            vals.append((-1) ** k)
        return outward(min(vals), max(vals))
    if name == "tan":
        if math.ceil((a - math.pi / 2) / math.pi) <= math.floor((b - math.pi / 2) / math.pi):
            raise ExpressionError("区间包含 tan 极点")
        return outward(math.tan(a), math.tan(b))
    if name == "log" and a <= 0 or name == "sqrt" and a < 0:
        raise ExpressionError("区间超出函数定义域")
    func = {"exp": math.exp, "log": math.log, "sqrt": math.sqrt}[name]
    return outward(func(a), func(b))


class RootExpression:
    def __init__(self, source: str, *, update=False):
        if not isinstance(source, str) or not 1 <= len(source) <= 200:
            raise ExpressionError("表达式须为 1–200 字符")
        try:
            self.root = ast.parse(source.replace("^", "**"), mode="eval").body
        except (SyntaxError, RecursionError) as exc:
            raise ExpressionError("请使用 x 和允许的算术函数") from exc
        nodes = list(ast.walk(self.root))
        if len(nodes) > 80:
            raise ExpressionError("表达式过于复杂")
        names = {"x", "pi", "e"} | ({"f", "df"} if update else set())
        for node in nodes:
            if isinstance(node, ast.Name):
                if node.id not in names | {"sin", "cos", "tan", "exp", "log", "sqrt", "abs"}:
                    raise ExpressionError("表达式包含不支持的名称")
            elif isinstance(node, ast.Constant):
                if type(node.value) not in (float, int) or not math.isfinite(node.value) or abs(node.value) > 1e100:
                    raise ExpressionError("不支持的常量")
            elif isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in {"sin", "cos", "tan", "exp", "log", "sqrt", "abs"} or len(node.args) != 1 or node.keywords:
                    raise ExpressionError("不支持的函数调用")
            elif isinstance(node, ast.BinOp):
                if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
                    raise ExpressionError("不支持的运算")
                if isinstance(node.op, ast.Pow):
                    exponent = node.right
                    sign = -1 if isinstance(exponent, ast.UnaryOp) and isinstance(exponent.op, ast.USub) else 1
                    exponent = exponent.operand if isinstance(exponent, ast.UnaryOp) else exponent
                    if not isinstance(exponent, ast.Constant) or type(exponent.value) not in (int, float) or int(exponent.value) != exponent.value or abs(sign * exponent.value) > 16:
                        raise ExpressionError("幂仅允许 -16 至 16 的整数")
            elif not isinstance(node, (ast.UnaryOp, ast.UAdd, ast.USub, ast.Load, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
                raise ExpressionError("禁止执行代码、属性或下标访问")

    def evaluate(self, x, *, derivative=False, f=None, df=None):
        env = {"x": x, "pi": math.pi, "e": math.e, "f": f, "df": df}

        def visit(node, depth=0):
            if depth > 20:
                raise ExpressionError("表达式嵌套过深")
            zero = interval(0) if isinstance(x, Interval) else 0.0
            if isinstance(node, ast.Constant):
                return node.value, zero
            if isinstance(node, ast.Name):
                if node.id not in env or env[node.id] is None:
                    raise ExpressionError("名称只能用作允许的函数调用")
                return env[node.id], interval(1) if isinstance(x, Interval) and node.id == "x" else 1.0 if node.id == "x" else zero
            if isinstance(node, ast.UnaryOp):
                value, slope = visit(node.operand, depth + 1)
                return (-value, -slope) if isinstance(node.op, ast.USub) else (value, slope)
            if isinstance(node, ast.Call):
                v, d = visit(node.args[0], depth + 1)
                name = node.func.id
                result = unary(name, v)
                if not derivative:
                    return result, zero
                if name == "sin": factor = unary("cos", v)
                elif name == "cos": factor = -unary("sin", v)
                elif name == "tan": factor = 1 + result ** 2
                elif name == "exp": factor = result
                elif name == "log": factor = interval(1) / v if isinstance(v, Interval) else 1 / v
                elif name == "sqrt": factor = interval(1) / (2 * result) if isinstance(v, Interval) else 1 / (2 * result)
                else:
                    if isinstance(v, Interval):
                        if v.lo <= 0 <= v.hi: raise ExpressionError("abs 在零点不可微")
                        factor = 1 if v.lo > 0 else -1
                    else:
                        if v == 0: raise ExpressionError("abs 在零点不可微")
                        factor = 1 if v > 0 else -1
                return result, factor * d
            a, da = visit(node.left, depth + 1)
            b, db = visit(node.right, depth + 1)
            if isinstance(node.op, ast.Add): return a + b, da + db
            if isinstance(node.op, ast.Sub): return a - b, da - db
            if isinstance(node.op, ast.Mult): return a * b, da * b + a * db if derivative else zero
            if isinstance(node.op, ast.Div): return a / b, (da * b - a * db) / (b ** 2) if derivative else zero
            return a ** b, b * (a ** (b - 1)) * da if derivative and b != 0 else zero

        try:
            value, slope = visit(self.root)
            result = slope if derivative else value
            if not isinstance(result, Interval) and (not math.isfinite(result) or abs(result) > 1e100):
                raise ExpressionError("计算结果非有限或超出数值预算")
            return interval(result) if isinstance(x, Interval) else result
        except (ArithmeticError, ValueError, TypeError) as exc:
            raise ExpressionError(str(exc)) from exc
