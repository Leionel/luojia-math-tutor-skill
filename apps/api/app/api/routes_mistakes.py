from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import Principal, get_principal, resolve_user_id
from app.config import Settings
from app.main_deps import get_app_settings, get_repository
from app.memory.repository import Repository
from app.tutor.exercise_generator import get_fallback_exercises


class MistakeCreate(BaseModel):
    subject: str
    concept: str | None = None
    mistake_code: str
    session_id: str | None = None


router = APIRouter(prefix="/api", tags=["mistakes"])


@router.get("/users/{user_id}/mistakes")
def list_user_mistakes(
    user_id: str,
    limit: int = 50,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
    return {"items": repo.list_user_mistakes(user_id, limit)}


@router.get("/users/{user_id}/mistakes/stats")
def get_mistake_stats(
    user_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
    return {"items": repo.get_mistake_stats(user_id)}


@router.post("/users/{user_id}/mistakes")
def create_mistake(
    user_id: str,
    body: MistakeCreate,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
    event_id = repo.add_mistake_event(
        user_id,
        body.session_id or "manual",
        body.subject,
        body.concept,
        body.mistake_code
    )
    return {"status": "ok", "event_id": event_id}

@router.post("/users/{user_id}/mistakes/{mistake_id}/generate-quiz")
def generate_quiz(
    user_id: str,
    mistake_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
    mistake = repo.get_mistake(mistake_id)
    if not mistake or mistake.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="未找到该错因记录")

    concept = mistake.get("concept", "未知考点")
    mistake_code = mistake.get("mistake_code", "")
    exercise = get_fallback_exercises(concept, difficulty=2, count=1)[0]
    prompt = (
        f"这是一道针对错因「{mistake_code}」的巩固练习，"
        f"对应知识点为 **{concept}**。\n\n"
        f"{exercise['text']}\n\n"
        "请先独立作答，不要直接查看答案。你可以把关键步骤发给我检查。"
    )

    return {"status": "ok", "quiz_content": prompt, "concept": concept}
