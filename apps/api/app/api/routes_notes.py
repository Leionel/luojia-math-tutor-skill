import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.main_deps import get_repository
from app.memory.repository import Repository

router = APIRouter(prefix="/api", tags=["notes"])


class GenerateNoteRequest(BaseModel):
    session_id: str


def _compact_text(content: str, limit: int = 320) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit].rstrip()}..."


def _latest_learning_meta(messages: list[dict]) -> dict:
    for message in reversed(messages):
        learning_meta = message.get("learning_meta")
        if message.get("role") == "assistant" and learning_meta:
            return learning_meta
    return {}


def _next_step(meta: dict) -> str:
    concepts = meta.get("concepts") or []
    concept = concepts[0] if concepts else "本节内容"
    if meta.get("verified") and meta.get("is_correct") is False:
        return f"先修正“{concept}”中的当前偏差，再独立重做一道同类题。"
    if meta.get("verified") and meta.get("is_correct") is True:
        return f"用一道稍高难度的“{concept}”题检验迁移能力。"
    if (meta.get("mastery_score") or 0.5) < 0.6:
        return f"先复述“{concept}”的关键条件，再完成一个最小例题。"
    return f"整理“{concept}”的方法步骤，并尝试独立解释每一步为什么成立。"


@router.post("/tutor/notes")
def generate_note(
    payload: GenerateNoteRequest,
    repo: Repository = Depends(get_repository),
):
    messages = repo.list_messages(payload.session_id)
    user_messages = [
        _compact_text(message["content"], 180)
        for message in messages
        if message.get("role") == "user"
        and message.get("content", "").strip()
    ]
    assistant_messages = [
        _compact_text(message["content"], 320)
        for message in messages
        if message.get("role") == "assistant"
        and message.get("content", "").strip()
    ]
    meta = _latest_learning_meta(messages)
    concepts = meta.get("concepts") or []
    if not concepts:
        objective = meta.get("learning_objective")
        concepts = [objective] if objective else ["待从后续学习中归纳"]

    questions = "\n".join(
        f"- {question}" for question in user_messages[-5:]
    ) or "- 当前会话还没有学生提问。"
    conclusions = "\n".join(
        f"- {answer}" for answer in assistant_messages[-3:]
    ) or "- 当前会话还没有形成可整理的结论。"
    concept_lines = "\n".join(f"- {concept}" for concept in concepts[:5])

    review_items = []
    if meta.get("verifier_summary"):
        review_items.append(meta["verifier_summary"])
    if meta.get("mistake"):
        review_items.append(f"已识别偏差：{meta['mistake']}")
    if meta.get("mastery_score") is not None:
        review_items.append(
            "当前掌握度："
            f"{round(float(meta['mastery_score']) * 100)}%"
            f"（{meta.get('mastery_label') or '待评估'}）"
        )
    review = "\n".join(
        f"- {_compact_text(item, 180)}" for item in review_items
    ) or "- 本轮没有触发可记录的验算或错因。"

    note_content = f"""# 随堂笔记

## 本节主题
{concept_lines}

## 学习问题
{questions}

## 核心结论与方法
{conclusions}

## 状态与易错提醒
{review}

## 下一步复习
- {_next_step(meta)}
"""
    return {"note": note_content}


class NoteCreate(BaseModel):
    session_id: str
    subject: str
    content: str


@router.post("/users/{user_id}/notes")
def save_note(
    user_id: str,
    body: NoteCreate,
    repo: Repository = Depends(get_repository),
):
    note_id = repo.save_note(
        user_id,
        body.session_id,
        body.subject,
        body.content,
    )
    return {"status": "ok", "note_id": note_id}


@router.get("/users/{user_id}/notes")
def list_notes(
    user_id: str,
    repo: Repository = Depends(get_repository),
):
    notes = repo.list_notes(user_id)
    return {"notes": notes}


@router.delete("/notes/{note_id}")
def delete_note(
    note_id: str,
    repo: Repository = Depends(get_repository),
):
    repo.delete_note(note_id)
    return {"status": "ok"}
