"""Textbook document → Course Graph candidate pipeline.

Stage ① is deterministic segmentation: MinerU markdown is split by headings
and by the structured markers textbooks use (定义/定理/引理/推论/证明/例/算法/注),
so every candidate carries an auditable provenance (document, section title).

Markers are split into their own units rather than attached to the preceding
one. A textbook theorem is a *pedagogical unit* whose proof and examples are
separate units linked by typed relations; merging them into one blob made
"this example supports that theorem" a string-concatenation fact instead of a
graph edge, and produced 9k-char units that no retrieval budget can use.

Stage ② builds GraphCandidate payloads directly aligned with the review
schema: NEW_UNIT with scope_level=unclassified, plus NEW_RELATION edges
(supports_proof / example_of / derives_from / part_of). Nothing enters the
canonical graph without teacher review. No LLM involved: textbook layout is
structured enough that rules cover the bulk, keeping the pipeline
reproducible and free.

Stage ③ is the existing review flow: candidates are fed into CandidateManager
as pending and reviewed on /admin/knowledge.

Relation direction is intuitive: source is the supporting unit, target is the
unit being supported (`proof --supports_proof--> theorem`). Note this differs
from the offline `knowledge/pipeline/relations.py`, which is only used by
`scripts/run_pipeline_m1.py` and bypasses review.
"""

import hashlib
import re
from dataclasses import dataclass, field

# Markers that start a new candidate unit. Checked before the generic heading
# branch: MinerU renders markers as headings, so `## 定义 1.1` is both.
# The trailing class keeps prose such as "注意了" or "例如" from matching.
_UNIT_TYPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("definition", re.compile(r"^#{0,4}\s*(定义|Definition)[\d\s.:：、]")),
    ("theorem", re.compile(r"^#{0,4}\s*(定理|Theorem)[\d\s.:：、]")),
    ("lemma", re.compile(r"^#{0,4}\s*(引理|Lemma)[\d\s.:：、]")),
    ("corollary", re.compile(r"^#{0,4}\s*(推论|Corollary)[\d\s.:：、]")),
    ("algorithm", re.compile(r"^#{0,4}\s*(算法|Algorithm)[\d\s.:：、]")),
    ("proof", re.compile(r"^#{0,4}\s*(证明|Proof)\b")),
    ("example", re.compile(r"^#{0,4}\s*(例\s*\d|例题|Example)\b")),
    ("remark", re.compile(r"^#{0,4}\s*(注|Remark)[\d\s.:：、]")),
]

_HEADING = re.compile(r"^(#{1,4})\s+(.+)$")

# MinerU flattens the outline: every heading in a real 150-page textbook came
# out as `##`, so the number of '#' carries no hierarchy at all. Recover the
# depth from the section numbering instead, which textbooks do carry.
_CHAPTER_HEADING = re.compile(r"^第\s*[0-9一二三四五六七八九十]+\s*章")
_NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)")


def _outline_depth(title: str, markdown_level: int) -> int:
    """Infer a heading's outline depth from its numbering, not its '#' count."""
    if _CHAPTER_HEADING.match(title):
        return 1
    numbered = _NUMBERED_HEADING.match(title)
    if numbered:
        # "2.1" -> 2, "2.1.3" -> 3
        return len(numbered.group(1).split("."))
    return markdown_level

# Which typed relation a supporting unit forms with its anchor.
_ANCHOR_RELATION = {
    "proof": "supports_proof",
    "example": "example_of",
    "corollary": "derives_from",
    "lemma": "supports_proof",
}

# Unit types that can serve as the anchor a proof/example/corollary refers to.
_ANCHOR_TYPES = frozenset({"definition", "theorem", "lemma"})

# Types whose content is verbatim textbook prose rather than a claim, so they
# link to the enclosing section instead of standing alone as concepts.
_SUPPORT_TYPES = frozenset({"proof", "example", "remark"})

_MIN_SECTION_CHARS = 40
# A typed marker line is itself structural evidence, and real textbooks carry
# short proofs and corollaries. Under the old attach behaviour these rode along
# inside their parent unit; now that they are separate atoms a 40-char floor
# would silently drop them.
_MIN_MARKER_CHARS = 12
_MAX_TITLE_CHARS = 60


def _is_kept(section: "DocumentSection") -> bool:
    limit = _MIN_SECTION_CHARS if section.unit_type == "concept" else _MIN_MARKER_CHARS
    return len(section.text.strip()) >= limit


@dataclass
class DocumentSection:
    title: str
    unit_type: str  # concept | definition | theorem | lemma | corollary | proof | example | algorithm | remark
    text: str
    order: int
    # Enclosing plain heading, used for `part_of`.
    parent_title: str | None = None
    # Heading path (chapter → section → subsection) the atom sits under.
    chapter_path: list[str] = field(default_factory=list)
    # Nearest preceding definition/theorem/lemma, used for support relations.
    anchor_title: str | None = None
    # Titles of anchors that follow this unit within the same section; a lemma
    # usually precedes the theorem it supports.
    following_anchor_titles: list[str] = field(default_factory=list)


def _marker_type(line: str) -> str | None:
    stripped = line.strip()
    return next(
        (name for name, pattern in _UNIT_TYPE_PATTERNS if pattern.match(stripped)),
        None,
    )


def segment_document(markdown: str) -> list[DocumentSection]:
    sections: list[DocumentSection] = []
    current_title = "引言"
    current_type = "concept"
    parent_title: str | None = None
    anchor_title: str | None = None
    buffer: list[str] = []
    # Heading text by markdown level, so an atom can report the chapter path it
    # sits under. A heading at level L replaces L and clears every deeper level.
    heading_stack: dict[int, str] = {}

    def chapter_path() -> list[str]:
        return [heading_stack[level] for level in sorted(heading_stack)]

    def flush() -> None:
        text = "\n".join(buffer).strip()
        if text:
            sections.append(
                DocumentSection(
                    title=current_title.strip(),
                    unit_type=current_type,
                    text=text,
                    order=len(sections),
                    parent_title=parent_title,
                    chapter_path=chapter_path(),
                    anchor_title=anchor_title,
                )
            )

    for line in markdown.splitlines():
        heading = _HEADING.match(line)
        unit_type = _marker_type(line)

        if unit_type:
            flush()
            current_title = line.strip().lstrip("#").strip()
            current_type = unit_type
            buffer = [line]
            if unit_type in _ANCHOR_TYPES:
                anchor_title = current_title
        elif heading:
            flush()
            current_title = heading.group(2)
            current_type = "concept"
            buffer = [line]
            # A plain heading opens a new section scope: it becomes the parent
            # of the markers inside it and resets the anchor, so a proof never
            # links across a section boundary to an unrelated theorem.
            parent_title = current_title
            anchor_title = None
            level = _outline_depth(current_title, len(heading.group(1)))
            heading_stack[level] = current_title
            for deeper in [key for key in heading_stack if key > level]:
                del heading_stack[deeper]
        else:
            buffer.append(line)
    flush()

    _link_lemmas_to_following_anchors(sections)
    return sections


def _link_lemmas_to_following_anchors(sections: list[DocumentSection]) -> None:
    """A lemma supports the next anchor in the same section, not the previous one."""
    for index, section in enumerate(sections):
        if section.unit_type != "lemma":
            continue
        for later in sections[index + 1:]:
            if later.parent_title != section.parent_title:
                break
            if later.unit_type in _ANCHOR_TYPES and later.title != section.title:
                section.following_anchor_titles.append(later.title)
                break


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.md5(":".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:10].upper()}"


def _keywords_from_title(title: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9\- ]{2,24}", title)[:5]


def _unit_id(document_id: str, section: DocumentSection) -> str:
    return _stable_id("DOC", document_id, section.title, section.text.strip())


def build_candidates_from_document(
    document_id: str,
    filename: str,
    markdown: str,
) -> list[dict]:
    """Turn parsed textbook markdown into NEW_UNIT and NEW_RELATION proposals.

    Candidate ids are stable content hashes, so re-uploading the same document
    increments support_count instead of duplicating proposals.
    """
    kept = [section for section in segment_document(markdown) if _is_kept(section)]
    unit_id_by_title: dict[str, str] = {}
    for section in kept:
        unit_id_by_title.setdefault(section.title, _unit_id(document_id, section))

    proposals: list[dict] = []
    for section in kept:
        text = section.text.strip()
        unit_id = unit_id_by_title[section.title]
        # Hash the text as well as the title: a textbook can repeat a heading
        # (two "证明" blocks, two "定义 2.1" in different editions), and
        # keying on title alone would collapse them into one candidate,
        # silently inflating support_count and dropping the second section.
        proposals.append(
            {
                "candidate_id": _stable_id("CAND_DOC", document_id, section.title, text),
                "candidate_type": "new_unit",
                "payload": {
                    "id": unit_id,
                    "title": section.title[:_MAX_TITLE_CHARS] or f"{filename} 片段 {section.order + 1}",
                    "type": section.unit_type,
                    # Full text, not a preview. A 600-char cap here discarded
                    # 75% of a real 150-page textbook's body text and cut 44 of
                    # 46 theorem proofs mid-LaTeX. Presentation and prompt
                    # layers apply their own limits via app.text_preview.
                    "content": text,
                    "keywords": _keywords_from_title(section.title),
                    "difficulty": 3,
                    # Provenance has to survive review, not just live on the
                    # candidate's evidence_ref: an approved unit that cannot say
                    # which document and section it came from is unauditable.
                    "chapter_path": section.chapter_path,
                    "context_header": " › ".join(section.chapter_path),
                    "source_document_id": document_id,
                    # Teacher decides the scope on review; the pipeline never
                    # promotes unreviewed textbook content to core.
                    "scope_level": "unclassified",
                    "teaching_role": "core",
                },
                "proposed_by": "document_pipeline",
                "evidence_ref": f"document:{document_id}:{section.title}",
            }
        )

    proposals.extend(_relation_proposals(document_id, kept, unit_id_by_title))
    return proposals


def _relation_proposals(
    document_id: str,
    kept: list[DocumentSection],
    unit_id_by_title: dict[str, str],
) -> list[dict]:
    """Emit typed edges so pedagogical links are graph facts, not concatenated text."""
    proposals: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(source_title: str, target_title: str, relation_type: str, confidence: float) -> None:
        source_id = unit_id_by_title.get(source_title)
        target_id = unit_id_by_title.get(target_title)
        if not source_id or not target_id or source_id == target_id:
            return
        key = (source_id, target_id, relation_type)
        if key in seen:
            return
        seen.add(key)
        proposals.append(
            {
                "candidate_id": _stable_id("CAND_REL", document_id, *key),
                "candidate_type": "new_relation",
                "payload": {
                    "source_unit_id": source_id,
                    "target_unit_id": target_id,
                    "relation_type": relation_type,
                    "confidence": confidence,
                },
                "proposed_by": "document_pipeline",
                "evidence_ref": f"document:{document_id}:{source_title}",
            }
        )

    for section in kept:
        # A proof/example/corollary supports the anchor it follows. Confidence
        # is below 1.0 because the link is positional, not read from the text.
        relation = _ANCHOR_RELATION.get(section.unit_type)
        if relation and section.anchor_title:
            add(section.title, section.anchor_title, relation, 0.8)

        # A lemma precedes the theorem it supports.
        if section.unit_type == "lemma":
            for following in section.following_anchor_titles:
                add(section.title, following, "supports_proof", 0.7)

        # Everything belongs to its enclosing section, giving the hierarchy
        # that small-to-big retrieval expands along.
        if section.parent_title and section.unit_type != "concept":
            add(section.title, section.parent_title, "part_of", 0.9)

    return proposals
