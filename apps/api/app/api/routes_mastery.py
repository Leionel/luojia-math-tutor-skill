from fastapi import APIRouter, Depends
from app.main_deps import get_repository
from app.memory.repository import Repository

router = APIRouter(prefix="/api", tags=["Mastery"])

@router.get("/users/{user_id}/mastery")
def get_user_mastery(user_id: str, repo: Repository = Depends(get_repository)):
    return {"items": repo.list_mastery(user_id)}

@router.get("/users/{user_id}/mastery/summary")
def get_user_mastery_summary(user_id: str, repo: Repository = Depends(get_repository)):
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
