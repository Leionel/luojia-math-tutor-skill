"""Textbook document → Course Graph candidate pipeline.

Stage ① is deterministic segmentation: MinerU markdown is split by headings
and by the structured markers textbooks use (定义/定理/算法), so every
candidate carries an auditable provenance (document, section title).

Stage ② builds GraphCandidate payloads directly aligned with the review
schema (NEW_UNIT with scope_level=unclassified), so nothing enters the
canonical graph without teacher review. No LLM involved in v1: textbook
layout is structured enough that rules cover the bulk, keeping the pipeline
reproducible and free.

Stage ③ is the existing review flow: candidates are fed into
CandidateManager as pending and reviewed on /admin/knowledge.
"""

import hashlib
import re
from dataclasses import dataclass

# Markers that start a new candidate unit inside a chapter.
_UNIT_TYPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("definition", re.compile(r"^#{0,4}\s*定义[\d\s.:：、]")),
    ("theorem", re.compile(r"^#{0,4}\s*(定理|Theorem)[\d\s.:：、]")),
    ("algorithm", re.compile(r"^#{0,4}\s*算法[\d\s.:：、]")),
]

_HEADING = re.compile(r"^(#{1,4})\s+(.+)$")

# These blocks belong to the unit announced just before them (a 证明 extends
# its 定理; an 例题 illustrates the current unit), so they never split.
_ATTACH_PATTERNS = (
    re.compile(r"^#{0,4}\s*(证明|Proof)\b"),
    re.compile(r"^#{0,4}\s*(例\s*\d|例题|Example)\b"),
    re.compile(r"^#{0,4}\s*(推论|注|Remark|Corollary)[\d\s.:：、]"),
)

_MIN_SECTION_CHARS = 40
_MAX_CONTENT_CHARS = 600
_MAX_TITLE_CHARS = 60


@dataclass
class DocumentSection:
    title: str
    unit_type: str  # concept | definition | theorem | algorithm
    text: str
    order: int


def segment_document(markdown: str) -> list[DocumentSection]:
    sections: list[DocumentSection] = []
    current_title = "引言"
    current_type = "concept"
    buffer: list[str] = []

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            sections.append(
                DocumentSection(
                    title=current_title.strip(),
                    unit_type=current_type,
                    text=text,
                    order=len(sections),
                )
            )

    for line in markdown.splitlines():
        heading = _HEADING.match(line)
        unit_type = next(
            (t for t, pattern in _UNIT_TYPE_PATTERNS if pattern.match(line.strip())),
            None,
        )
        attach = any(pattern.match(line.strip()) for pattern in _ATTACH_PATTERNS)

        if heading and not attach:
            flush()
            current_title = heading.group(2)
            current_type = "concept"
            buffer = [line]
        elif unit_type:
            flush()
            current_title = line.strip().lstrip("#").strip()
            current_type = unit_type
            buffer = [line]
        else:
            buffer.append(line)
    flush()
    return sections


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.md5(":".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:10].upper()}"


def _keywords_from_title(title: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9\- ]{2,24}", title)[:5]


def build_candidates_from_document(
    document_id: str,
    filename: str,
    markdown: str,
) -> list[dict]:
    """Turn parsed textbook markdown into NEW_UNIT candidate proposals.

    Candidate ids are stable content hashes, so re-uploading the same
    document increments support_count instead of duplicating proposals.
    """
    proposals: list[dict] = []
    for section in segment_document(markdown):
        text = section.text.strip()
        if len(text) < _MIN_SECTION_CHARS:
            continue
        proposals.append(
            {
                "candidate_id": _stable_id("CAND_DOC", document_id, section.title),
                "candidate_type": "new_unit",
                "payload": {
                    "id": _stable_id("DOC", document_id, section.title),
                    "title": section.title[:_MAX_TITLE_CHARS] or f"{filename} 片段 {section.order + 1}",
                    "type": section.unit_type,
                    "content": text[:_MAX_CONTENT_CHARS],
                    "keywords": _keywords_from_title(section.title),
                    "difficulty": 3,
                    # Teacher decides the scope on review; the pipeline never
                    # promotes unreviewed textbook content to core.
                    "scope_level": "unclassified",
                    "teaching_role": "core",
                },
                "proposed_by": "document_pipeline",
                "evidence_ref": f"document:{document_id}:{section.title}",
            }
        )
    return proposals
