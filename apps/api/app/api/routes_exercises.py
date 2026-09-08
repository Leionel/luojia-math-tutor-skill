from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import Principal, get_principal, resolve_user_id
from app.config import Settings
from app.main_deps import get_app_settings, get_repository
from app.memory.repository import Repository
from app.tutor.exercise_generator import get_fallback_exercises


router = APIRouter(prefix="/api", tags=["exercises"])


class SimilarExerciseRequest(BaseModel):
    user_id: str = "demo-user"
    concept: str
    difficulty: int = 2
    count: int = 2


@router.post("/exercises/similar")
def similar_exercises(
    payload: SimilarExerciseRequest,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    resolve_user_id(principal, payload.user_id, settings)
    exercises = get_fallback_exercises(payload.concept, payload.difficulty, payload.count)
    return {"exercises": exercises}
