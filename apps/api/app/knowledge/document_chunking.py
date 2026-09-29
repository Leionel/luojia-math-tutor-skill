"""Structure-aware chunking of parsed textbook markdown for FTS retrieval.

Chunks are a *derived retrieval artifact*. `documents.markdown` is the source of
truth and chunks must never be re-joined to reconstruct a document: each chunk
carries a context header that is not part of the body, so the concatenation is
deliberately not the original text.

The previous implementation was a 500-character fixed window with a 50-character
overlap. It cut through headings and LaTeX, and the overlap meant the rejoined
text was 11.3% longer than the source on a real 150-page textbook — which is
what produced duplicate candidates and inflated `support_count`.

Chunking here follows the same segmentation the candidate pipeline uses, so a
chunk never straddles two pedagogical units, and long sections split at
paragraph boundaries with a LaTeX-safe cut as the last resort.
"""

from app.knowledge.candidate_pipeline import segment_document
from app.text_preview import safe_cut

# Retrieval granularity. Small enough that a hit is about one idea, large enough
# that a theorem statement plus its opening steps stay together.
MAX_CHUNK_CHARS = 1200
# Below this a piece is merged into its predecessor rather than emitted alone.
MIN_CHUNK_CHARS = 120
# Tolerance when merging a stub tail, so the merge cannot itself overshoot badly.
_MERGE_SLACK = 1.25


def _split_body(body: str, max_chars: int) -> list[str]:
    """Split one section body at paragraph boundaries, preserving all text."""
    if len(body) <= max_chars:
        return [body]

    pieces: list[str] = []
    current = ""
    for paragraph in body.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            pieces.append(current)
            current = ""
        if len(paragraph) <= max_chars:
            current = paragraph
            continue
        # A single oversized paragraph (a long display-math derivation): cut at
        # safe boundaries rather than at an arbitrary character offset.
        remaining = paragraph
        while len(remaining) > max_chars:
            cut = safe_cut(remaining, max_chars) or remaining[:max_chars]
            pieces.append(cut)
            remaining = remaining[len(cut):].lstrip()
        current = remaining
    if current:
        pieces.append(current)

    merged: list[str] = []
    for piece in pieces:
        if (
            merged
            and len(piece) < MIN_CHUNK_CHARS
            and len(merged[-1]) + len(piece) <= max_chars * _MERGE_SLACK
        ):
            merged[-1] = f"{merged[-1]}\n\n{piece}"
        else:
            merged.append(piece)
    return merged


def chunk_document(
    markdown: str,
    max_chars: int = MAX_CHUNK_CHARS,
) -> list[str]:
    """Split parsed markdown into retrieval chunks, one pedagogical unit at a time.

    Every chunk is prefixed with its chapter path and section title so a hit can
    be attributed without a second lookup. No overlap: text appears exactly once.
    """
    chunks: list[str] = []
    for section in segment_document(markdown):
        body = section.text.strip()
        if not body:
            continue
        header = " › ".join(part for part in section.chapter_path if part)
        prefix = f"[{header}] {section.title}\n" if header else f"{section.title}\n"
        for piece in _split_body(body, max_chars):
            piece = piece.strip()
            if piece:
                chunks.append(prefix + piece)
    return chunks
