import ast
import asyncio
import os
import sys
import tempfile

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
_CHILD_FLAGS = ("-E", "-P")


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

async def execute_python_code(code: str, timeout: int = 10) -> str:
    """
    Executes Python code in a separate subprocess and captures stdout/stderr.
    Useful for SymPy math verification.
    """
    timeout = max(1, min(int(timeout), 10))
    validation_error = _validate_math_code(code)
    if validation_error:
        return validation_error

    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        temp_file_path = f.name

    try:
        import subprocess
        # Run subprocess in a separate thread to avoid blocking the event loop,
        # and to support WindowsSelectorEventLoopPolicy which doesn't support create_subprocess_exec.
        def run_proc():
            return subprocess.run(
                _child_command(temp_file_path),
                capture_output=True,
                timeout=timeout,
                text=True
            )
            
        try:
            process = await asyncio.to_thread(run_proc)
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out after {timeout} seconds."
            
        out_str = process.stdout.strip()[:_MAX_OUTPUT_CHARS]
        err_str = process.stderr.strip()[:_MAX_OUTPUT_CHARS]

        # A missing interpreter dependency is an environment fault, not a
        # student-code fault. Surface it distinctly so the verification hard
        # gate can report "verification unavailable" instead of blaming the
        # submitted code for something it cannot influence.
        dependency_error = _missing_dependency_error(err_str)
        if dependency_error:
            return dependency_error

        result = ""
        if out_str:
            result += f"Output:\n{out_str}\n"
        if err_str:
            result += f"Error:\n{err_str}\n"
            
        if not result:
            result = "Code executed successfully with no output."
            
        return result

    except Exception as e:
        return f"Execution Error: {str(e)}"
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
