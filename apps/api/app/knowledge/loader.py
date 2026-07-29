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
    "m1_linear_algebra_ch5_units.json": "linear_algebra",
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
    has_published = (output_dir / "published_knowledge.json").exists()
    
    for path in sorted(output_dir.glob("*.json")):
        if has_published and path.name.startswith("m1_"):
            continue
            
        subject = SUBJECT_BY_FILE.get(path.name, "general")
        parsed_data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(parsed_data, dict) and "units" in parsed_data:
            raw_items = parsed_data["units"]
        elif isinstance(parsed_data, list):
            raw_items = parsed_data
        else:
            continue
        for index, raw in enumerate(raw_items):
            if not isinstance(raw, dict):
                continue
            item_id = _text(raw.get("id")) or f"{path.stem}_{index}"
            description = _text(raw.get("description") or raw.get("core_content_latex") or raw.get("content"))
            chapter_path = raw.get("chapter_path")
            chapter_str = " -> ".join(chapter_path) if isinstance(chapter_path, list) else _text(raw.get("chapter"))
            items.append(
                KnowledgeItem(
                    id=item_id,
                    subject=raw.get("subject") or subject,
                    source_file=path.name,
                    concept_zh=_text(raw.get("concept_zh") or raw.get("name") or raw.get("title")),
                    prerequisite=_list(raw.get("prerequisite") or raw.get("expected_prerequisites")),
                    description=description,
                    intuitive_explanation=_text(raw.get("intuitive_explanation")),
                    solution=_text(raw.get("solution")),
                    type=_text(raw.get("type")) or "concept",
                    chapter=chapter_str,
                    section=_text(raw.get("section")),
                    related_exercises=_list(raw.get("related_exercises")),
                    difficulty=int(raw.get("difficulty", 3)) if str(raw.get("difficulty", 3)).isdigit() else 3,
                    source=raw.get("source") if isinstance(raw.get("source"), dict) else {},
                )
            )
    return tuple(items)


@lru_cache
def load_knowledge_units(course_id: str = "default_course"):
    """Load all knowledge items and convert them into Schema v1 KnowledgeUnit objects with stable prerequisite IDs."""
    items = load_knowledge()
    name_to_id_map: dict[str, str] = {}
    for item in items:
        if item.concept_zh:
            name_to_id_map[item.concept_zh] = item.id

    units = [item.to_unit(course_id=course_id, prereq_id_map=name_to_id_map) for item in items]
    return tuple(units)

@lru_cache
def load_knowledge_relations() -> tuple[Any, ...]:
    output_dir = get_settings().knowledge_root / "output"
    relations = []
    has_published = (output_dir / "published_knowledge.json").exists()
    
    for path in sorted(output_dir.glob("*.json")):
        if has_published and path.name.startswith("m1_"):
            continue
            
        try:
            parsed_data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(parsed_data, dict) and "relations" in parsed_data:
                from app.knowledge.schema import KnowledgeRelation
                for r in parsed_data["relations"]:
                    relations.append(
                        KnowledgeRelation(
                            source_unit_id=r.get("source_unit_id", ""),
                            target_unit_id=r.get("target_unit_id", ""),
                            relation_type=r.get("relation_type", ""),
                            confidence=float(r.get("confidence", 1.0)),
                            provenance=r.get("provenance", "rule"),
                            review_status=r.get("review_status", "verified")
                        )
                    )
        except Exception:
            pass
            
    return tuple(relations)
