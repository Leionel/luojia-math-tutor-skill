import ast
import asyncio
import os
import sys
import tempfile
import subprocess
import time
from app.agents.tool_result import ToolExecutionResult

_ALLOWED_IMPORT_ROOTS = {"math", "sympy"}
_MAX_CODE_CHARS = 8_000
_MAX_OUTPUT_CHARS = 16_000
_ALLOWED_CALL_NAMES = {
    "Abs",
    "Eq",
    "Function",
    "Integral",
    "Limit",
    "Matrix",
    "Rational",
    "S",
    "Symbol",
    "acos",
    "asin",
    "atan",
    "cos",
    "diff",
    "expand",
    "exp",
    "factor",
    "integrate",
    "limit",
    "log",
    "nsimplify",
    "pi",
    "print",
    "simplify",
    "sin",
    "solve",
    "sqrt",
    "symbols",
    "tan",
}
_DENIED_NAMES = {
    "__builtins__",
    "__import__",
    "breakpoint",
    "compile",
    "delattr",
    "dir",
    "eval",
    "exec",
    "exit",
    "getattr",
    "globals",
    "help",
    "input",
    "locals",
    "memoryview",
    "object",
    "open",
    "quit",
    "setattr",
    "type",
    "vars",
}
_DENIED_NODES = (
    ast.AsyncFor,
    ast.AsyncFunctionDef,
    ast.AsyncWith,
    ast.ClassDef,
    ast.Delete,
    ast.For,
    ast.FunctionDef,
    ast.Global,
    ast.Lambda,
    ast.Nonlocal,
    ast.Raise,
    ast.Try,
    ast.While,
    ast.With,
)

# Interpreter flags for the sandboxed child process.
#
# ``-I`` must NOT be used here: it implies ``-s``, which drops *user*
# site-packages. When dependencies are installed with ``pip install --user``
# (the default on many Windows setups) ``sympy`` then becomes unimportable in
# the child, so every ``[VERIFY]`` round fails and the symbolic verification
# path silently degrades. Keep only the two parts of ``-I`` that provide
# isolation:
#   ``-E``  ignore PYTHON* environment variables (blocks PYTHONPATH injection)
#   ``-P``  do not prepend the script's directory or cwd to sys.path
# Import reachability is already constrained by the AST allowlist above, which
# permits only ``math`` and ``sympy`` roots.
_CHILD_FLAGS = ("-E", "-P", "-X", "utf8")


def _child_command(script_path: str) -> list[str]:
    """Build the argv used to run sandboxed code. Exposed for tests."""
    return [sys.executable, *_CHILD_FLAGS, script_path]


def _missing_dependency_error(err_str: str) -> str | None:
    """Classify a child traceback caused by an unavailable allowed dependency.

    Returns an explicit environment-fault message, or ``None`` when stderr does
    not indicate a missing ``math``/``sympy`` installation.
    """
    for module in sorted(_ALLOWED_IMPORT_ROOTS):
        if f"No module named '{module}'" in err_str:
            return (
                f"Error: sandbox environment is missing '{module}'. "
                "Symbolic verification is unavailable; install the API "
                "dependencies into the interpreter that runs the server."
            )
    return None


def _import_root(name: str) -> str:
    return name.split(".", 1)[0]


def _validate_math_code(code: str) -> str | None:
    if len(code) > _MAX_CODE_CHARS:
        return f"Error: code exceeds {_MAX_CODE_CHARS} characters."
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"Error: invalid Python syntax ({exc.msg})."

    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, _DENIED_NODES):
            return f"Error: unsupported statement type ({type(node).__name__})."

        if isinstance(node, ast.Import):
            for alias in node.names:
                root = _import_root(alias.name)
                if root not in _ALLOWED_IMPORT_ROOTS:
                    return "Error: only math and sympy imports are allowed."
                imported_modules.add(alias.asname or root)

        if isinstance(node, ast.ImportFrom):
            root = _import_root(node.module or "")
            if root not in _ALLOWED_IMPORT_ROOTS:
                return "Error: only math and sympy imports are allowed."
            if any(alias.name == "*" for alias in node.names):
                return "Error: wildcard imports are not allowed."

        if isinstance(node, ast.Name):
            if node.id in _DENIED_NAMES or node.id.startswith("__"):
                return f"Error: unsafe name is not allowed ({node.id})."

        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                return f"Error: private attributes are not allowed ({node.attr})."

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                if func.id not in _ALLOWED_CALL_NAMES:
                    return f"Error: function call is not allowed ({func.id})."
            elif isinstance(func, ast.Attribute):
                root = func.value
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name) and root.id in _DENIED_NAMES:
                    return f"Error: unsafe call target is not allowed ({root.id})."
            else:
                return "Error: dynamic call targets are not allowed."

    return None

async def execute_python_result(code: str, timeout: int = 10) -> ToolExecutionResult:
    """Run allowlisted math code; cancellation kills and reaps the child.

    The threaded communicate works on Windows SelectorEventLoop too. The
    process handle remains owned here, so cancelling an await cannot orphan it.
    This is execution evidence, not a mathematical proof or a C0 acceptance.
    """
    started = time.perf_counter()
    timeout = max(1, min(int(timeout), 10))
    validation_error = _validate_math_code(code)
    if validation_error:
        return ToolExecutionResult("rejected", stderr=validation_error, error_code="code_rejected")

    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        temp_file_path = f.name

    process = None
    communication = None
    try:
        process = subprocess.Popen(_child_command(temp_file_path), stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        communication = asyncio.create_task(asyncio.to_thread(process.communicate, timeout=timeout))
        try:
            out_str, err_str = await asyncio.shield(communication)
        except subprocess.TimeoutExpired:
            if process.poll() is None:
                process.kill()
            await asyncio.to_thread(process.communicate)
            return ToolExecutionResult("timeout", stderr=f"Code execution timed out after {timeout} seconds.",
                                       exit_code=process.returncode, error_code="tool_timeout",
                                       duration_ms=round((time.perf_counter() - started) * 1000, 2))
        out_str = out_str.strip()[:_MAX_OUTPUT_CHARS]
        err_str = err_str.strip()[:_MAX_OUTPUT_CHARS]

        # A missing interpreter dependency is an environment fault, not a
        # student-code fault. Surface it distinctly so the verification hard
        # gate can report "verification unavailable" instead of blaming the
        # submitted code for something it cannot influence.
        dependency_error = _missing_dependency_error(err_str)
        if dependency_error:
            return ToolExecutionResult("unavailable", out_str, dependency_error, process.returncode,
                                       "tool_dependency_missing", round((time.perf_counter() - started) * 1000, 2))
        succeeded = process.returncode == 0
        return ToolExecutionResult("succeeded" if succeeded else "failed", out_str,
                                   err_str or ("" if succeeded else f"Code exited with status {process.returncode}."),
                                   process.returncode, None if succeeded else "tool_execution_failed",
                                   round((time.perf_counter() - started) * 1000, 2))
    except asyncio.CancelledError:
        if process is not None and process.poll() is None:
            process.kill()
        if communication is not None:
            await asyncio.gather(communication, return_exceptions=True)
        raise
    except Exception:
        return ToolExecutionResult("unavailable", stderr="Math execution is unavailable.",
                                   error_code="tool_unavailable")
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            await asyncio.to_thread(process.wait)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


async def execute_python_code(code: str, timeout: int = 10) -> str:
    """Compatibility display wrapper; runtime decisions use the typed result."""
    return (await execute_python_result(code, timeout)).to_legacy_text()
