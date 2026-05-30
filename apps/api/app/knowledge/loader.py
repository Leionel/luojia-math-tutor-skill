import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.knowledge.schema import KnowledgeItem


SUBJECT_BY_FILE = {
    "concept_gs.json": "calculus",
    "ex.json": "calculus",
    "la.json": "linear_algebra",
    "proba.json": "probability",
    "Proba_example.json": "probability",
}


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    return str(value)


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if value:
        return [str(value)]
    return []


@lru_cache
def load_knowledge() -> tuple[KnowledgeItem, ...]:
    output_dir = get_settings().knowledge_root / "output"
    items: list[KnowledgeItem] = []
    for path in sorted(output_dir.glob("*.json")):
        subject = SUBJECT_BY_FILE.get(path.name, "general")
        raw_items = json.loads(path.read_text(encoding="utf-8"))
        for index, raw in enumerate(raw_items):
            item_id = _text(raw.get("id")) or f"{path.stem}_{index}"
            description = _text(raw.get("description") or raw.get("core_content_latex"))
            items.append(
                KnowledgeItem(
                    id=item_id,
                    subject=subject,
                    source_file=path.name,
                    concept_zh=_text(raw.get("concept_zh") or raw.get("name")),
                    prerequisite=_list(raw.get("prerequisite")),
                    description=description,
                    intuitive_explanation=_text(raw.get("intuitive_explanation")),
                    solution=_text(raw.get("solution")),
                )
            )
    return tuple(items)

