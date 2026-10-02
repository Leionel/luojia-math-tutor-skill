from functools import lru_cache

from app.config import Settings, get_settings
from app.memory.repository import Repository
from app.tutor.orchestrator import TutorOrchestrator


def get_app_settings() -> Settings:
    return get_settings()


def ensure_reference_help_allowed(owner: str, allowed_probe_id: str | None = None) -> None:
    from fastapi import HTTPException
    from app.tutor.help_boundary import assert_reference_help_allowed
    try:
        assert_reference_help_allowed(owner, allowed_probe_id=allowed_probe_id)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@lru_cache
def get_repository() -> Repository:
    return Repository(get_settings())


@lru_cache
def get_orchestrator() -> TutorOrchestrator:
    return TutorOrchestrator(get_settings(), get_repository())

