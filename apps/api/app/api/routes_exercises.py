from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.main_deps import get_repository
from app.memory.repository import Repository
from app.tutor.exercise_generator import get_fallback_exercises


router = APIRouter(prefix="/api", tags=["exercises"])


class SimilarExerciseRequest(BaseModel):
    user_id: str = "demo-user"
    concept: str
    difficulty: int = 2
    count: int = 2


@router.post("/exercises/similar")
def similar_exercises(payload: SimilarExerciseRequest, repo: Repository = Depends(get_repository)):
    exercises = get_fallback_exercises(payload.concept, payload.difficulty, payload.count)
    return {"exercises": exercises}
