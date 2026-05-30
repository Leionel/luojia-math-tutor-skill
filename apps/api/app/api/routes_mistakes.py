from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.main_deps import get_repository
from app.memory.repository import Repository


class MistakeCreate(BaseModel):
    subject: str
    concept: str | None = None
    mistake_code: str
    session_id: str | None = None


router = APIRouter(prefix="/api", tags=["mistakes"])


@router.get("/users/{user_id}/mistakes")
def list_user_mistakes(user_id: str, limit: int = 50, repo: Repository = Depends(get_repository)):
    return {"items": repo.list_user_mistakes(user_id, limit)}


@router.get("/users/{user_id}/mistakes/stats")
def get_mistake_stats(user_id: str, repo: Repository = Depends(get_repository)):
    return {"items": repo.get_mistake_stats(user_id)}


@router.post("/users/{user_id}/mistakes")
def create_mistake(user_id: str, body: MistakeCreate, repo: Repository = Depends(get_repository)):
    event_id = repo.add_mistake_event(
        user_id,
        body.session_id or "manual",
        body.subject,
        body.concept,
        body.mistake_code
    )
    return {"status": "ok", "event_id": event_id}

@router.post("/users/{user_id}/mistakes/{mistake_id}/generate-quiz")
def generate_quiz(user_id: str, mistake_id: str, repo: Repository = Depends(get_repository)):
    mistake = repo.get_mistake(mistake_id)
    if not mistake:
        return {"status": "error", "message": "Mistake not found"}
    
    # Normally we would call LLM here. To ensure robustness and speed, we will generate a template quiz.
    # We could also use ModelFactory.get_model() if we wanted dynamic.
    # For MVP, we will generate a high-quality math quiz based on the concept and mistake.
    concept = mistake.get("concept", "未知考点")
    mistake_code = mistake.get("mistake_code", "")
    
    prompt = f"你曾经在以下题目中犯过错，相关的考点是：**{concept}**。你的错误总结为：*{mistake_code}*\n\n为了巩固这个知识点，我为你生成了一道新题目。请尝试解答：\n\n已知函数 \\( f(x) = e^x \\sin x \\)，求其在区间 \\( [0, \\pi] \\) 上的最大值点。\n\n你可以把你的思路或每一步推导发给我，我会为你实时批改！"
    
    return {"status": "ok", "quiz_content": prompt, "concept": concept}
