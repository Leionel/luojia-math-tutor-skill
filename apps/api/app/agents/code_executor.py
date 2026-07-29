import ast
import asyncio
import os
import sys
import tempfile

_ALLOWED_IMPORT_ROOTS = {"math", "sympy"}
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


def _import_root(name: str) -> str:
    return name.split(".", 1)[0]


def _validate_math_code(code: str) -> str | None:
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
                [sys.executable, "-I", temp_file_path],
                capture_output=True,
                timeout=timeout,
                text=True
            )
            
        try:
            process = await asyncio.to_thread(run_proc)
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out after {timeout} seconds."
            
        out_str = process.stdout.strip()
        err_str = process.stderr.strip()
        
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
