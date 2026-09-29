from pathlib import Path

import pytest

from app.agents.code_executor import (
    _CHILD_FLAGS,
    _child_command,
    _missing_dependency_error,
    execute_python_code,
)


@pytest.mark.asyncio
async def test_code_executor_allows_basic_sympy() -> None:
    code = """
from sympy import Eq, solve, symbols
x = symbols("x")
print(solve(Eq(x + 1, 3), x))
"""

    result = await execute_python_code(code)

    assert "Output:" in result
    assert "[2]" in result


@pytest.mark.asyncio
async def test_code_executor_rejects_file_access(tmp_path: Path) -> None:
    marker = tmp_path / "pwned.txt"

    result = await execute_python_code(f"open(r'{marker}', 'w').write('x')")

    assert "unsafe name" in result or "not allowed" in result
    assert not marker.exists()


@pytest.mark.asyncio
async def test_code_executor_rejects_non_math_import(tmp_path: Path) -> None:
    marker = tmp_path / "pwned.txt"
    code = f"""
from pathlib import Path
Path(r"{marker}").write_text("x")
"""

    result = await execute_python_code(code)

    assert "only math and sympy imports are allowed" in result
    assert not marker.exists()


@pytest.mark.asyncio
async def test_code_executor_rejects_dunder_import_escape() -> None:
    result = await execute_python_code("__import__('os').system('echo pwned')")

    assert "unsafe name" in result or "not allowed" in result


@pytest.mark.asyncio
async def test_code_executor_rejects_eval_escape() -> None:
    result = await execute_python_code("eval(\"__import__('os').system('echo pwned')\")")

    assert "unsafe name" in result or "not allowed" in result


@pytest.mark.asyncio
async def test_code_executor_rejects_getattr_escape() -> None:
    result = await execute_python_code("globals()\n")

    assert "unsafe name" in result or "not allowed" in result


@pytest.mark.asyncio
async def test_code_executor_rejects_builtin_shadowing_escape(tmp_path: Path) -> None:
    marker = tmp_path / "pwned.txt"
    code = f"""
import sympy
getattr(sympy, 'Symbol')
open(r'{marker}', 'w').write('x')
"""

    result = await execute_python_code(code)

    assert "unsafe name" in result or "not allowed" in result
    assert not marker.exists()


def test_child_flags_keep_isolation_without_hiding_user_site() -> None:
    """`-I` implies `-s`, which hides user site-packages and breaks sympy.

    Regression guard for the bug where every `[VERIFY]` round failed on
    machines whose dependencies were installed with `pip install --user`.
    """
    assert "-I" not in _CHILD_FLAGS
    assert "-s" not in _CHILD_FLAGS
    # Env-var path injection and script-dir prepending must stay blocked.
    assert "-E" in _CHILD_FLAGS
    assert "-P" in _CHILD_FLAGS


def test_child_command_targets_current_interpreter_and_script() -> None:
    import sys

    argv = _child_command("/tmp/probe.py")

    assert argv[0] == sys.executable
    assert argv[-1] == "/tmp/probe.py"
    assert argv[1:-1] == list(_CHILD_FLAGS)


def test_missing_dependency_error_flags_environment_fault() -> None:
    stderr = (
        "Traceback (most recent call last):\n"
        '  File "probe.py", line 2, in <module>\n'
        "    from sympy import symbols\n"
        "ModuleNotFoundError: No module named 'sympy'\n"
    )

    message = _missing_dependency_error(stderr)

    assert message is not None
    assert "sandbox environment is missing 'sympy'" in message
    assert "unavailable" in message


def test_missing_dependency_error_ignores_ordinary_student_errors() -> None:
    stderr = (
        "Traceback (most recent call last):\n"
        '  File "probe.py", line 3, in <module>\n'
        "NameError: name 'y' is not defined\n"
    )

    assert _missing_dependency_error(stderr) is None
