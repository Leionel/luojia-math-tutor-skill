"""Textbook document → Course Graph candidate pipeline.

Stage ① is deterministic segmentation: MinerU markdown is split by headings
and by the structured markers textbooks use (定义/定理/引理/推论/证明/例/算法/注),
so every candidate carries an auditable provenance (document, chapter path).

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
    # 命题 is a claim with a proof, i.e. an anchor just like 定理. Keeping the
    # label in the title preserves the distinction for a human reviewer.
    ("theorem", re.compile(r"^#{0,4}\s*(命题|Proposition)[\d\s.:：、]")),
    ("lemma", re.compile(r"^#{0,4}\s*(引理|Lemma)[\d\s.:：、]")),
    ("corollary", re.compile(r"^#{0,4}\s*(推论|Corollary)[\d\s.:：、]")),
    ("algorithm", re.compile(r"^#{0,4}\s*(算法|Algorithm)[\d\s.:：、]")),
    ("proof", re.compile(r"^#{0,4}\s*(证明|Proof)\b")),
    ("example", re.compile(r"^#{0,4}\s*(例\s*\d|例题|Example)\b")),
    ("remark", re.compile(r"^#{0,4}\s*(注|Remark)[\d\s.:：、]")),
]

_HEADING = re.compile(r"^(#{1,4})\s+(.+)$")

# A marker line often carries the whole sentence after the number, e.g.
# "例题 1.1 (1) 多项式计算通常较为简单，我们可以设计一个算法：". The title should be
# the label plus its number and short parenthetical name, not that sentence.
_MARKER_TITLE = re.compile(
    r"^#{0,4}\s*"
    r"(定义|定理|命题|引理|推论|算法|证明|注|例题|例|Definition|Theorem|Proposition"
    r"|Lemma|Corollary|Algorithm|Proof|Remark|Example)"
    r"\s*(\d+(?:\.\d+)*)?"
    r"(?:\s*[（(]\s*([^）)]{2,48})\s*[）)])?"
)

# Headings that place a unit inside the numbered outline of the book.
_CHAPTER_HEADING = re.compile(r"^第\s*[0-9一二三四五六七八九十]+\s*章")
# `search` variant: OCR decorates some real headings, e.g. "K第 1 章 练习 k",
# which are legitimate exercise sections and must not be mistaken for front
# matter just because the chapter label is not at the very start.
_CHAPTER_ANYWHERE = re.compile(r"第\s*[0-9一二三四五六七八九十]+\s*章")
_NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)")

# Back matter inherits the last chapter's path, which would make it look like
# numbered content. Resetting the outline on these headings lets the structural
# front-matter test drop them as well. Deliberately a closed, conventional set:
# inferring "this heading is back matter" would also catch legitimate
# unnumbered sections such as "(1) 复化梯形公式".
_BACK_MATTER = re.compile(r"^(参考文献|附录|索引|致谢|后记)")

# Which typed relation a supporting unit forms with its anchor.
_ANCHOR_RELATION = {
    "proof": "supports_proof",
    "example": "example_of",
    "corollary": "derives_from",
    "lemma": "supports_proof",
}

# Unit types that can serve as the anchor a proof/example/corollary refers to.
_ANCHOR_TYPES = frozenset({"definition", "theorem", "lemma"})

_MIN_SECTION_CHARS = 40
# A typed marker line is itself structural evidence, and real textbooks carry
# short proofs and corollaries. Under the old attach behaviour these rode along
# inside their parent unit; now that they are separate atoms a 40-char floor
# would silently drop them.
_MIN_MARKER_CHARS = 12
_MAX_TITLE_CHARS = 60
# A trailing fragment after "label number" is kept as the unit's name only if it
# is short and carries no sentence punctuation — "算法 2.1 二分法" is a name,
# "例题 1.1 (1) 多项式计算通常较为简单，我们可以设计一个算法：" is prose.
_MAX_NAME_CHARS = 24
_SENTENCE_PUNCTUATION = "。；，、：,;:！？!?"


@dataclass
class DocumentSection:
    title: str
    unit_type: str  # concept | definition | theorem | lemma | corollary | proof | example | algorithm | remark
    text: str
    order: int
    # Heading path (chapter → section → subsection) the atom sits under.
    chapter_path: list[str] = field(default_factory=list)
    # Index of the enclosing plain heading, used for `part_of`.
    parent_order: int | None = None
    # Index of the nearest preceding definition/theorem/lemma.
    anchor_order: int | None = None
    # Indexes of anchors that follow this unit within the same section; a lemma
    # usually precedes the theorem it supports.
    following_anchor_orders: list[int] = field(default_factory=list)


def _marker_type(line: str) -> str | None:
    stripped = line.strip()
    return next(
        (name for name, pattern in _UNIT_TYPE_PATTERNS if pattern.match(stripped)),
        None,
    )


def _outline_depth(title: str, markdown_level: int) -> int:
    """Infer a heading's outline depth from its numbering, not its '#' count.

    MinerU flattens the outline: all 158 headings of a real 150-page textbook
    came out as `##`, so the markdown level carries no hierarchy at all.
    """
    if _CHAPTER_HEADING.match(title):
        return 1
    numbered = _NUMBERED_HEADING.match(title)
    if numbered:
        # "2.1" -> 2, "2.1.3" -> 3
        return len(numbered.group(1).split("."))
    return markdown_level


def _marker_title(line: str) -> str:
    """Reduce a marker line to `label number（name）`.

    Falls back to the raw line when it does not match, so an unusual marker is
    still legible rather than silently retitled.
    """
    stripped = line.strip()
    match = _MARKER_TITLE.match(stripped)
    if not match:
        return stripped.lstrip("#").strip()

    label, number, paren = match.group(1), match.group(2), match.group(3)
    title = f"{label} {number}" if number else label
    # "(1)" is an enumeration, not a name; only keep meaningful parentheticals.
    if paren and not paren.strip().isdigit():
        title = f"{title}（{paren.strip()}）"
        return title

    remainder = stripped[match.end():].strip().lstrip("#").strip()
    if (
        remainder
        and len(remainder) <= _MAX_NAME_CHARS
        and not any(char in remainder for char in _SENTENCE_PUNCTUATION)
    ):
        title = f"{title} {remainder}"
    return title.strip()


def _is_numbered_context(title: str) -> bool:
    return bool(_CHAPTER_ANYWHERE.search(title) or _NUMBERED_HEADING.match(title))


def segment_document(markdown: str) -> list[DocumentSection]:
    sections: list[DocumentSection] = []
    current_title = "引言"
    current_type = "concept"
    current_is_heading = False
    buffer: list[str] = []
    # Heading text by outline depth, so an atom can report the chapter path it
    # sits under. A heading at depth D replaces D and clears every deeper level.
    heading_stack: dict[int, str] = {}
    last_heading_order: int | None = None
    last_anchor_order: int | None = None

    def chapter_path() -> list[str]:
        return [heading_stack[depth] for depth in sorted(heading_stack)]

    def flush() -> None:
        nonlocal last_heading_order, last_anchor_order
        text = "\n".join(buffer).strip()
        if not text:
            return
        order = len(sections)
        sections.append(
            DocumentSection(
                title=current_title.strip(),
                unit_type=current_type,
                text=text,
                order=order,
                chapter_path=chapter_path(),
                parent_order=last_heading_order,
                anchor_order=last_anchor_order,
            )
        )
        if current_is_heading:
            last_heading_order = order
        if current_type in _ANCHOR_TYPES:
            last_anchor_order = order

    for line in markdown.splitlines():
        heading = _HEADING.match(line)
        unit_type = _marker_type(line)

        if unit_type:
            flush()
            current_title = _marker_title(line)
            current_type = unit_type
            current_is_heading = False
            buffer = [line]
        elif heading:
            flush()
            current_title = heading.group(2)
            current_type = "concept"
            current_is_heading = True
            buffer = [line]
            # A plain heading opens a new section scope: it becomes the parent
            # of the markers inside it and resets the anchor, so a proof never
            # links across a section boundary to an unrelated theorem.
            last_anchor_order = None
            if _BACK_MATTER.match(current_title):
                # Back matter sits outside the numbered outline; without this
                # reset it inherits the last chapter's path and the structural
                # front-matter test cannot tell it apart from real content.
                heading_stack.clear()
            depth = _outline_depth(current_title, len(heading.group(1)))
            heading_stack[depth] = current_title
            for deeper in [key for key in heading_stack if key > depth]:
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
            if later.parent_order != section.parent_order:
                break
            if later.unit_type in _ANCHOR_TYPES and later.order != section.order:
                section.following_anchor_orders.append(later.order)
                break


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.md5(":".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:10].upper()}"


def _keywords_from_title(title: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9\- ]{2,24}", title)[:5]


def _unit_id(document_id: str, section: DocumentSection) -> str:
    return _stable_id("DOC", document_id, section.title, section.text.strip())


def _has_length(section: DocumentSection) -> bool:
    limit = _MIN_SECTION_CHARS if section.unit_type == "concept" else _MIN_MARKER_CHARS
    return len(section.text.strip()) >= limit


def _is_front_matter(section: DocumentSection) -> bool:
    """True for title page, 前言, 目录, 引言 and 参考文献.

    Identified structurally rather than by a word list: such a section sits
    outside the numbered outline, so its chapter path contains no chapter or
    numbered heading. Chapter introductions ("第 1 章 基础知识") do have one and
    are kept, since they carry real teaching content.
    """
    if section.unit_type != "concept":
        return False
    return not any(_is_numbered_context(part) for part in section.chapter_path)


def build_candidates_from_document(
    document_id: str,
    filename: str,
    markdown: str,
) -> list[dict]:
    """Turn parsed textbook markdown into NEW_UNIT and NEW_RELATION proposals.

    Candidate ids are stable content hashes, so re-uploading the same document
    increments support_count instead of duplicating proposals.
    """
    kept = [
        section
        for section in segment_document(markdown)
        if _has_length(section) and not _is_front_matter(section)
    ]
    # Relations resolve endpoints by section order, not by title: normalized
    # marker titles collide (a book has 56 separate "证明"), and keying on title
    # would point every proof relation at the same unit.
    unit_id_by_order: dict[int, str] = {
        section.order: _unit_id(document_id, section) for section in kept
    }

    proposals: list[dict] = []
    for section in kept:
        text = section.text.strip()
        unit_id = unit_id_by_order[section.order]
        # Hash the text as well as the title: a textbook can repeat a heading,
        # and keying on title alone would collapse distinct sections into one
        # candidate, silently inflating support_count and dropping content.
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

    proposals.extend(_relation_proposals(document_id, kept, unit_id_by_order))
    return proposals


def _relation_proposals(
    document_id: str,
    kept: list[DocumentSection],
    unit_id_by_order: dict[int, str],
) -> list[dict]:
    """Emit typed edges so pedagogical links are graph facts, not concatenated text."""
    title_by_order = {section.order: section.title for section in kept}
    proposals: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(source_order: int | None, target_order: int | None, relation_type: str, confidence: float) -> None:
        if source_order is None or target_order is None:
            return
        source_id = unit_id_by_order.get(source_order)
        target_id = unit_id_by_order.get(target_order)
        # An endpoint dropped by the length or front-matter filter cannot be
        # linked; skip rather than emit a dangling edge.
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
                    "source_title": title_by_order.get(source_order, ""),
                    "target_title": title_by_order.get(target_order, ""),
                },
                "proposed_by": "document_pipeline",
                "evidence_ref": f"document:{document_id}:{title_by_order.get(source_order, '')}",
            }
        )

    for section in kept:
        # A proof/example/corollary supports the anchor it follows. Confidence
        # is below 1.0 because the link is positional, not read from the text.
        relation = _ANCHOR_RELATION.get(section.unit_type)
        if relation:
            add(section.order, section.anchor_order, relation, 0.8)

        # A lemma precedes the theorem it supports.
        if section.unit_type == "lemma":
            for following in section.following_anchor_orders:
                add(section.order, following, "supports_proof", 0.7)

        # Everything belongs to its enclosing section, giving the hierarchy
        # that small-to-big retrieval expands along.
        if section.unit_type != "concept":
            add(section.order, section.parent_order, "part_of", 0.9)

    return proposals
