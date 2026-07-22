import re
from typing import Any
from app.knowledge.schema import KnowledgeUnit


def extract_units_from_markdown(
    markdown_text: str,
    source_document_id: str,
    course_id: str = "default_course",
) -> list[KnowledgeUnit]:
    """
    Rule-based & Page-aware extractor for converting parsed Markdown into KnowledgeUnit Schema v1 objects.
    Looks for page markers like `<!-- PAGE: x -->` and section headers/type tags.
    """
    units: list[KnowledgeUnit] = []
    lines = markdown_text.splitlines()

    current_page = 1
    current_chapter = ""
    current_section = ""
    current_unit_lines: list[str] = []
    current_unit_title = ""
    current_unit_type = "concept"
    current_page_start = 1

    # Regular expressions for types
    type_patterns = {
        "定义": r"^(定义|Definition)\b",
        "定理": r"^(定理|Theorem)\b",
        "证明": r"^(证明|Proof)\b",
        "例题": r"^(例|例题|Example)\b",
        "习题": r"^(习题|Exercise)\b",
    }

    def flush_unit():
        nonlocal current_unit_lines, current_unit_title, current_unit_type, current_page_start
        if not current_unit_lines:
            return

        content = "\n".join(current_unit_lines).strip()
        if not content:
            return

        unit_id = f"ku_{source_document_id}_{len(units) + 1:04d}"
        title = current_unit_title or f"Unit {len(units) + 1}"
        
        chapter_path = [p for p in [current_chapter, current_section] if p]

        unit = KnowledgeUnit(
            id=unit_id,
            course_id=course_id,
            schema_version="v1",
            type=current_unit_type,
            title=title,
            content=content,
            source_document_id=source_document_id,
            page_start=current_page_start,
            page_end=current_page,
            source_span={
                "source_document_id": source_document_id,
                "page_start": current_page_start,
                "page_end": current_page,
                "quote": content[:120] + "..." if len(content) > 120 else content,
            },
            chapter_path=chapter_path,
            keywords=[title] if title else [],
            provenance="rule",
            review_status="draft",
        )
        units.append(unit)
        current_unit_lines = []
        current_unit_title = ""

    for line in lines:
        page_match = re.search(r"<!--\s*PAGE:\s*(\d+)\s*-->", line, re.IGNORECASE)
        if page_match:
            current_page = int(page_match.group(1))
            continue

        # Chapter / Section tracking
        if line.startswith("# "):
            current_chapter = line.lstrip("# ").strip()
            continue
        elif line.startswith("## "):
            current_section = line.lstrip("# ").strip()
            continue

        # Check for start of new Knowledge Unit (e.g. ### 定义 5.1 或 **定理 1**)
        clean_line = line.lstrip("#* ").strip()
        matched_type = None
        for t_name, pattern in type_patterns.items():
            if re.search(pattern, clean_line, re.IGNORECASE):
                matched_type = t_name
                break

        if matched_type:
            flush_unit()
            current_unit_type = matched_type
            current_unit_title = clean_line
            current_page_start = current_page
            current_unit_lines.append(line)
        else:
            if current_unit_lines:
                current_unit_lines.append(line)

    flush_unit()
    return units
