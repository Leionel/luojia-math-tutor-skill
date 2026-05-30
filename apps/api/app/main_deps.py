from functools import lru_cache

from app.config import Settings, get_settings
from app.memory.repository import Repository
from app.tutor.orchestrator import TutorOrchestrator


def get_app_settings() -> Settings:
    return get_settings()


@lru_cache
def get_repository() -> Repository:
    return Repository(get_settings())


@lru_cache
def get_orchestrator() -> TutorOrchestrator:
    return TutorOrchestrator(get_settings(), get_repository())

