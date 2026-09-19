import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import (
    Principal,
    ensure_session_access,
    get_principal,
    resolve_user_id,
)
from app.config import Settings
from app.llm.openai_compatible import OpenAICompatibleClient
from app.main_deps import get_app_settings, get_repository
from app.memory.repository import Repository

router = APIRouter(prefix="/api", tags=["notes"])


class GenerateNoteRequest(BaseModel):
    session_id: str


class DocumentNoteRequest(BaseModel):
    document_id: str
    # When set, the note weaves in the student's most recent mistake concepts
    # so the textbook material is organized around their weak spots.
    with_mistakes: bool = False


# Budget for a single-pass LLM note: the heading outline keeps the global
# structure, the sampled content covers beginning/middle/end of the book.
_NOTE_CHAR_BUDGET = 24_000
_MAX_HEADINGS = 80


def _sample_chunks(chunks: list[str], char_budget: int = _NOTE_CHAR_BUDGET) -> str:
    total = sum(len(c) for c in chunks)
    if total <= char_budget:
        return "\n".join(chunks)
    ratio = char_budget / total
    parts: list[str] = []
    used = 0
    for chunk in chunks:
        keep = max(1, int(len(chunk) * ratio))
        parts.append(chunk[:keep])
        used += keep
        if used >= char_budget:
            break
    return "\n".join(parts)


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
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    # Preserve the existing direct-call service contract used by local tools;
    # FastAPI replaces these dependency markers during real HTTP requests.
    if not isinstance(settings, Settings):
        settings = get_app_settings()
    if not isinstance(principal, Principal):
        principal = Principal(settings.demo_user_id, False)
    ensure_session_access(payload.session_id, principal, settings, repo)
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


@router.post("/users/{user_id}/notes/from-document")
async def generate_document_note(
    user_id: str,
    body: DocumentNoteRequest,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    # Same direct-call compatibility as generate_note above.
    if not isinstance(settings, Settings):
        settings = get_app_settings()
    if not isinstance(principal, Principal):
        principal = Principal(settings.demo_user_id, False)
    user_id = resolve_user_id(principal, user_id, settings)

    doc = repo.get_document(body.document_id, user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document was not found.")
    chunks = repo.list_document_chunks(body.document_id)
    if not chunks:
        raise HTTPException(status_code=400, detail="该文档尚未完成解析，稍后再试。")

    markdown = "\n".join(chunks)
    headings = [
        line.strip()
        for line in markdown.splitlines()
        if line.lstrip().startswith("#")
    ][:_MAX_HEADINGS]
    sample = _sample_chunks(chunks)

    mistake_section = ""
    if body.with_mistakes:
        mistakes = repo.list_user_mistakes(user_id, limit=5)
        concepts = [m.get("concept") or m.get("mistake_code", "") for m in mistakes]
        concepts = [c for c in concepts if c]
        if concepts:
            mistake_section = (
                "\n【学生近期错题薄弱概念】请在“建议复习路径”中优先安排这些概念：\n- "
                + "\n- ".join(concepts)
                + "\n"
            )

    prompt = f"""你是一名数学教辅编辑。下面是一本教材的解析结果（标题大纲与抽样正文）。请整理成一份结构化学习笔记，直接输出 Markdown，包含以下小节：
# 《{doc['filename']}》学习笔记
## 一、全书章节脉络
## 二、核心定义与定理（公式用 LaTeX）
## 三、关键公式与方法速查
## 四、典型例题与易错点
## 五、建议复习路径
要求：忠实于给定材料，不要编造原文中不存在的定理、公式或例题；材料未覆盖的内容明确标注“（原文未覆盖）”。
{mistake_section}
【标题大纲】
{chr(10).join(headings) or "（解析结果中未识别到标题）"}

【正文抽样】
{sample}"""

    client = OpenAICompatibleClient(settings)
    try:
        note = await client.chat_completion([{"role": "user", "content": prompt}])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"笔记生成失败：{exc}") from exc

    note_id = repo.save_note(
        user_id,
        f"document:{body.document_id}",
        doc["filename"],
        note,
    )
    return {"status": "ok", "note_id": note_id, "note": note}


@router.post("/users/{user_id}/notes")
def save_note(
    user_id: str,
    body: NoteCreate,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
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
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
    notes = repo.list_notes(user_id)
    return {"notes": notes}


@router.delete("/notes/{note_id}")
def delete_note(
    note_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    if (principal.authenticated or settings.auth_required) and not repo.note_belongs_to(
        note_id,
        principal.user_id,
    ):
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Note was not found.")
    repo.delete_note(note_id)
    return {"status": "ok"}
