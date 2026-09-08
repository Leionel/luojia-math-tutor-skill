from fastapi import APIRouter, Depends
from app.auth import Principal, get_principal, resolve_user_id
from app.config import Settings
from app.main_deps import get_app_settings, get_repository
from app.memory.repository import Repository

router = APIRouter(prefix="/api", tags=["Mastery"])

@router.get("/users/{user_id}/mastery")
def get_user_mastery(
    user_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
    return {"items": repo.list_mastery(user_id)}

@router.get("/users/{user_id}/mastery/summary")
def get_user_mastery_summary(
    user_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
    items = repo.list_mastery(user_id)
    if not items:
        return {"total_concepts": 0, "average_score": 0.0, "weak_concepts": []}
    total_score = sum(item["score"] for item in items)
    weak_concepts = [{"concept": item["concept"], "score": item["score"]} for item in items if item["score"] < 0.6]
    return {
        "total_concepts": len(items), 
        "average_score": total_score / len(items),
        "weak_concepts": weak_concepts
    }
