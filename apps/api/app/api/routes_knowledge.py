from collections import Counter

from fastapi import APIRouter

from app.knowledge.loader import load_knowledge


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


TYPE_LABELS = {
    "concept": "概念",
    "definition": "定义",
    "theorem": "定理",
    "proof": "证明",
    "example": "例题",
    "exercise": "练习",
    "algorithm": "算法",
    "common_mistake": "易错点",
    "mistake": "易错点",
}


def knowledge_type_label(value: str) -> str:
    normalized = value.strip().lower().replace(" ", "_")
    if normalized in TYPE_LABELS:
        return TYPE_LABELS[normalized]
    for marker, label in (
        ("定义", "定义"),
        ("定理", "定理"),
        ("证明", "证明"),
        ("例", "例题"),
        ("练习", "练习"),
        ("算法", "算法"),
        ("易错", "易错点"),
    ):
        if marker in value:
            return label
    return "其他"


@router.get("/catalog")
def get_knowledge_catalog():
    items_by_id = {}
    for item in load_knowledge():
        description = " ".join(item.description.split())
        if len(description) > 240:
            description = f"{description[:237]}..."
        candidate = {
            "id": item.id,
            "subject": item.subject,
            "type": item.type,
            "type_label": knowledge_type_label(item.type),
            "title": item.concept_zh,
            "chapter": item.chapter,
            "section": item.section,
            "description": description,
            "prerequisites": item.prerequisite,
            "difficulty": item.difficulty,
        }
        existing = items_by_id.get(item.id)
        candidate_detail = sum(
            bool(candidate[field])
            for field in ("chapter", "section", "description", "prerequisites")
        )
        existing_detail = sum(
            bool(existing[field])
            for field in ("chapter", "section", "description", "prerequisites")
        ) if existing else -1
        if candidate_detail > existing_detail:
            items_by_id[item.id] = candidate

    items = list(items_by_id.values())

    items.sort(
        key=lambda item: (
            item["subject"],
            item["type_label"],
            item["chapter"],
            item["title"],
        )
    )
    subject_counts = Counter(item["subject"] for item in items)
    type_counts = Counter(item["type_label"] for item in items)
    return {
        "items": items,
        "facets": {
            "subjects": dict(sorted(subject_counts.items())),
            "types": dict(sorted(type_counts.items())),
        },
        "total": len(items),
    }
