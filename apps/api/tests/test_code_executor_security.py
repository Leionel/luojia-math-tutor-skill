from pathlib import Path

import pytest

from app.agents.code_executor import execute_python_code


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
