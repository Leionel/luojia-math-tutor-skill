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

from app.config import ENV_FILE, load_env_file

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


def test_keys_from_the_real_env_file_are_visible_after_import() -> None:
    """Guard for the original bug: importing `app.config` must load `.env`."""
    if not ENV_FILE.is_file():
        pytest.skip("apps/api/.env is not present in this environment")

    keys = [
        line.split("=", 1)[0].strip()
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#") and "=" in line
    ]
    assert keys, "apps/api/.env declares no keys"

    # Only key *names* are reported; values are never read or printed.
    missing = [key for key in keys if key not in os.environ]
    assert not missing, f".env keys not loaded into os.environ: {missing}"
