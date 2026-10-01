from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth import Principal, get_principal, resolve_user_id
from app.config import Settings
from app.knowledge.loader import load_knowledge
from app.main_deps import get_app_settings, get_repository
from app.memory.repository import Repository

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchResultItem(BaseModel):
    id: str
    category: str  # "curriculum" | "mistakes" | "notes"
    category_label: str
    title: str
    subtitle: str
    content: str
    formula: str | None = None
    metadata: dict[str, Any] = {}


class GlobalSearchResponse(BaseModel):
    query: str
    category: str
    total: int
    items: list[SearchResultItem]


CATEGORY_LABELS = {
    "curriculum": "教材定理",
    "mistakes": "错题复盘",
    "notes": "随堂笔记",
}


def _matches_query(query_terms: list[str], text: str) -> bool:
    if not query_terms:
        return True
    text_lower = text.lower()
    return any(term in text_lower for term in query_terms)


@router.get("/global", response_model=GlobalSearchResponse)
def search_global(
    q: str = Query(..., min_length=1, description="搜索关键词或公式片段"),
    category: str = Query("all", description="分类：all | curriculum | mistakes | notes"),
    limit: int = Query(20, ge=1, le=100),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, None, settings)
    terms = [term.lower() for term in q.strip().split() if term.strip()]
    results: list[SearchResultItem] = []

    # 1. 搜索教材与知识图谱 (curriculum)
    if category in ("all", "curriculum"):
        for item in load_knowledge():
            title = getattr(item, "concept_zh", "") or getattr(item, "id", "")
            desc = getattr(item, "description", "") or ""
            formula = getattr(item, "latex_formula", None) or getattr(item, "solution", "") or ""
            chap = f"{getattr(item, 'chapter', '')} {getattr(item, 'section', '')}".strip()
            subject = getattr(item, "subject", "")
            searchable = f"{title} {desc} {formula} {subject} {chap}"

            if _matches_query(terms, searchable):
                score = 0
                title_lower = title.lower()
                for term in terms:
                    if term in title_lower:
                        score += 5
                    if term in formula.lower():
                        score += 3
                    if term in desc.lower():
                        score += 1

                results.append(
                    SearchResultItem(
                        id=f"curr_{item.id}",
                        category="curriculum",
                        category_label=CATEGORY_LABELS["curriculum"],
                        title=title,
                        subtitle=f"{item.subject} · {chap}" if chap else item.subject,
                        content=desc[:240] + ("..." if len(desc) > 240 else ""),
                        formula=formula if formula else None,
                        metadata={"type": item.type, "score": score, "raw_id": item.id},
                    )
                )

    # 2. 搜索错题本 (mistakes)
    if category in ("all", "mistakes"):
        try:
            mistakes = repo.list_user_mistakes(user_id, limit=50)
            for m in mistakes:
                m_dict = dict(m) if not isinstance(m, dict) else m
                concept = m_dict.get("concept") or "错题记录"
                subject = m_dict.get("subject") or "高等数学"
                code = m_dict.get("mistake_code") or ""
                reason = m_dict.get("reason") or m_dict.get("notes") or ""
                searchable = f"{concept} {subject} {code} {reason}"

                if _matches_query(terms, searchable):
                    results.append(
                        SearchResultItem(
                            id=f"mistake_{m_dict.get('id', '')}",
                            category="mistakes",
                            category_label=CATEGORY_LABELS["mistakes"],
                            title=f"错题 · {concept}",
                            subtitle=f"{subject} · 题号/编码 {code}",
                            content=reason or f"错题类型：{code}，建议回炉重造相应知识点。",
                            formula=None,
                            metadata={"score": 2, "raw_id": str(m_dict.get("id", ""))},
                        )
                    )
        except Exception:
            pass

    # 3. 搜索随堂笔记 (notes)
    if category in ("all", "notes"):
        try:
            notes = repo.list_notes(user_id)
            for n in notes:
                n_dict = dict(n) if not isinstance(n, dict) else n
                sub = n_dict.get("subject") or "复习笔记"
                content = n_dict.get("content") or ""
                searchable = f"{sub} {content}"

                if _matches_query(terms, searchable):
                    results.append(
                        SearchResultItem(
                            id=f"note_{n_dict.get('id', '')}",
                            category="notes",
                            category_label=CATEGORY_LABELS["notes"],
                            title=f"笔记 · {sub}",
                            subtitle=f"会话笔记 {n_dict.get('session_id', '')[:8]}",
                            content=content[:240] + ("..." if len(content) > 240 else ""),
                            formula=None,
                            metadata={"score": 2, "raw_id": str(n_dict.get("id", ""))},
                        )
                    )
        except Exception:
            pass

    # 按相关度评分降序排序，并截取 limit
    results.sort(key=lambda x: x.metadata.get("score", 0), reverse=True)
    results = results[:limit]

    return GlobalSearchResponse(
        query=q,
        category=category,
        total=len(results),
        items=results,
    )
