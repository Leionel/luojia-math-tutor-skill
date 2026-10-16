"""Regression coverage for `.env` loading.

The FastAPI app used to read configuration exclusively through `os.getenv`
while nothing loaded `apps/api/.env` — only `scripts/evaluate_benchmark.py`
did. `npm run dev:api` therefore started with empty `LLM_API_KEY` and
`MINERU_API_KEY` even when `.env` was filled in correctly, which made every
MinerU document upload fail with "MINERU_API_KEY is not configured".
"""

import os
from pathlib import Path

import pytest
from dotenv import dotenv_values

from app.config import ENV_FILE, NO_DOTENV_ENV_VAR, autoload_env_file, load_env_file

_PROBE_LOADED = "LUOJIA_ENV_PROBE_LOADED"
_PROBE_OVERRIDE = "LUOJIA_ENV_PROBE_OVERRIDE"


def test_env_file_resolves_to_apps_api_dotenv() -> None:
    assert ENV_FILE.name == ".env"
    assert ENV_FILE.parent.name == "api"
    assert ENV_FILE.parent.parent.name == "apps"


def test_load_env_file_reads_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"{_PROBE_LOADED}=from_dotenv\n", encoding="utf-8")
    monkeypatch.delenv(_PROBE_LOADED, raising=False)

    assert load_env_file(env_file) == env_file
    assert os.environ[_PROBE_LOADED] == "from_dotenv"


def test_load_env_file_does_not_override_real_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real environment variable must win over the dotenv file."""
    env_file = tmp_path / ".env"
    env_file.write_text(f"{_PROBE_OVERRIDE}=from_dotenv\n", encoding="utf-8")
    monkeypatch.setenv(_PROBE_OVERRIDE, "from_shell")

    load_env_file(env_file)

    assert os.environ[_PROBE_OVERRIDE] == "from_shell"


def test_load_env_file_returns_none_when_absent(tmp_path: Path) -> None:
    assert load_env_file(tmp_path / "does-not-exist.env") is None


def test_autoload_honours_the_opt_out_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The suite must never inherit a developer's real credentials."""
    env_file = tmp_path / ".env"
    env_file.write_text(f"{_PROBE_LOADED}=from_dotenv\n", encoding="utf-8")
    monkeypatch.delenv(_PROBE_LOADED, raising=False)

    assert autoload_env_file(env_file, disabled=True) is None
    assert _PROBE_LOADED not in os.environ

    assert autoload_env_file(env_file, disabled=False) == env_file
    assert os.environ[_PROBE_LOADED] == "from_dotenv"


def test_autoload_reads_the_gate_from_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"{_PROBE_LOADED}=from_dotenv\n", encoding="utf-8")
    monkeypatch.delenv(_PROBE_LOADED, raising=False)

    monkeypatch.setenv(NO_DOTENV_ENV_VAR, "1")
    assert autoload_env_file(env_file) is None
    assert _PROBE_LOADED not in os.environ

    monkeypatch.delenv(NO_DOTENV_ENV_VAR)
    assert autoload_env_file(env_file) == env_file
    assert os.environ[_PROBE_LOADED] == "from_dotenv"


def test_conftest_disables_dotenv_for_the_suite() -> None:
    assert os.environ.get(NO_DOTENV_ENV_VAR) == "1"
    assert not os.environ.get("LLM_API_KEY")
    assert not os.environ.get("MINERU_API_KEY")


def test_real_env_file_is_parseable_at_the_resolved_path() -> None:
    """Guard for the original bug: ENV_FILE must point at the file developers fill in.

    Parsed with `dotenv_values`, which never mutates `os.environ`, so real
    credentials cannot leak into the test process. Only key names are handled.
    """
    if not ENV_FILE.is_file():
        pytest.skip("apps/api/.env is not present in this environment")

    keys = sorted(key for key in dotenv_values(ENV_FILE) if key)
    assert keys, "apps/api/.env declares no keys"

    declared = sorted(
        line.split("=", 1)[0].strip()
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#") and "=" in line
    )
    assert keys == declared
