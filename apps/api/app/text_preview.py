"""Length limits for display and prompt rendering.

Truncation belongs here, at the edge, never in stored knowledge: cutting a
textbook unit at write time loses the proof permanently, while cutting at
render time only affects what one caller sees.

Cutting at an arbitrary character offset also produces unrenderable LaTeX —
`... + \frac { f ( x ^ { * } ) -` has an unclosed `\frac{`, which KaTeX rejects
outright. Showing less is better than showing something broken.
"""

import re

_TRAILING_COMMAND = re.compile(r"\\[A-Za-z]*$")


def _back_off_to_safe_boundary(cut: str) -> str:
    """Undo a cut that would split a math span or a LaTeX command."""
    for delimiter in ("$$", "$"):
        if cut.count(delimiter) % 2 == 1:
            index = cut.rfind(delimiter)
            if index > 0:
                cut = cut[:index]
            break

    # An unbalanced brace means the cut landed inside `\frac{...}` or similar.
    while cut.count("{") > cut.count("}"):
        index = cut.rfind("{")
        if index <= 0:
            break
        cut = cut[:index]

    # Drop trailing command tokens. Removing only a *partial* command would
    # leave a complete but argument-less one (`\operatorname`), which renders
    # no better than the fragment it replaced. Trailing whitespace is stripped
    # first, otherwise the end-of-string anchor never matches.
    cut = cut.rstrip()
    while True:
        match = _TRAILING_COMMAND.search(cut)
        if not match:
            break
        cut = cut[: match.start()].rstrip()

    return cut


def safe_cut(text: str, limit: int) -> str:
    """Return the longest prefix of `text` within `limit` that ends cleanly.

    Backs off to a paragraph, line or word boundary and refuses to leave an
    unbalanced math span, an unbalanced brace or a trailing command token.
    Returns `text` unchanged when it already fits.
    """
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text

    cut = _back_off_to_safe_boundary(text[:limit])

    # Prefer the largest structural boundary that still keeps most of the text.
    for separator in ("\n\n", "\n", " ", "\u3000"):
        index = cut.rfind(separator)
        if index > limit // 2:
            cut = cut[:index]
            break

    return cut.rstrip()


def truncate_text(text: str, limit: int, ellipsis: str = "…") -> str:
    """Truncate for display; returns `text` unchanged when it already fits."""
    if limit <= 0:
        return ""
    cut = safe_cut(text, limit)
    return text if cut == text else cut + ellipsis
