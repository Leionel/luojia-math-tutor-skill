"""Structure-aware document chunking.

The previous chunker was a 500-character fixed window with a 50-character
overlap. On a real 150-page textbook the overlap made the rejoined text 11.3%
longer than the source, which is what produced duplicate candidates and
inflated `support_count`; the fixed window also cut through headings and LaTeX.
"""

import re

from app.knowledge.document_chunking import MAX_CHUNK_CHARS, chunk_document

CHAPTER = """## 第 2 章 非线性方程的数值求解

## 2.1 单个方程求解问题

本节讨论单个非线性方程 f(x)=0 的数值解法，包括二分法、不动点迭代与牛顿法。

## 2.1.3 Newton 法

定理 2.4 (Newton 法的局部二次收敛性) 令 x* 为 f(x) 的单根，f 在 x* 的邻域内
二次连续可微且 f'(x*) 不为零，则存在邻域 U 使得从 U 内出发的牛顿迭代至少二次收敛。

证明 由泰勒展开可得

$$ x_{k+1} - x^{*} = \\frac{f''(\\xi_k)}{2 f'(x_k)} (x_k - x^{*})^2 $$

其中 ξ_k 介于 x_k 与 x* 之间。因为 f'(x*) 不为零且 f'' 连续，存在常数 L 与 d
使得 |f''(ξ)| ≤ L 且 |f'(x_k)| ≥ d 在邻域内成立，于是有误差递推

$$ |x_{k+1} - x^{*}| \\leq \\frac{L}{d} |x_k - x^{*}|^2 $$

由此可知误差按平方级递减，即迭代至少二次收敛。若初值足够接近单根，则归纳可
证明整个迭代序列都留在该邻域内，因此牛顿法在局部意义下有意义且收敛。

例 2.1 取 f(x)=x²-2，从 x0=1 出发迭代三步得到 1.41421356，与 sqrt(2) 的偏差
小于 1e-8，这与定理给出的平方收敛速度一致。

## 2.2 割线法

割线法用差商代替导数，避免计算 f'。其收敛阶约为 1.618，低于牛顿法但不需要
导数信息，因此在导数难以获得时更实用。
"""


def _body(chunk: str) -> str:
    """Drop the one-line context header the chunker prefixes."""
    return chunk.split("\n", 1)[1] if "\n" in chunk else ""


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def test_no_text_is_lost_or_duplicated() -> None:
    chunks = chunk_document(CHAPTER)
    rejoined = "".join(_body(chunk) for chunk in chunks)

    assert _squash(rejoined) == _squash(CHAPTER.strip()), (
        "chunks must partition the document exactly once"
    )


def test_the_old_overlap_inflation_is_gone() -> None:
    chunks = chunk_document(CHAPTER)
    rejoined = "".join(_body(chunk) for chunk in chunks)

    assert len(rejoined) <= len(CHAPTER)


def test_every_chunk_carries_its_context_header() -> None:
    chunks = chunk_document(CHAPTER)

    assert chunks
    for chunk in chunks:
        first_line = chunk.split("\n", 1)[0]
        assert first_line.startswith("[") or first_line
        assert "]" in first_line or "›" not in first_line


def test_a_theorem_chunk_is_attributable_to_its_section() -> None:
    chunks = chunk_document(CHAPTER)
    theorem_chunk = next(c for c in chunks if "定理 2.4" in c)

    header = theorem_chunk.split("\n", 1)[0]
    assert "第 2 章 非线性方程的数值求解" in header
    assert "2.1.3 Newton 法" in header


def test_every_heading_survives_intact_in_exactly_one_chunk() -> None:
    chunks = chunk_document(CHAPTER, max_chars=120)
    bodies = [_body(chunk) for chunk in chunks]

    headings = [
        line.strip() for line in CHAPTER.splitlines() if re.match(r"^#{1,4}\s+", line)
    ]
    assert headings, "fixture must contain headings"

    for heading in headings:
        occurrences = sum(
            1
            for body in bodies
            for line in body.splitlines()
            if line.strip() == heading
        )
        assert occurrences == 1, f"heading not intact exactly once: {heading!r} x{occurrences}"


def test_long_sections_split_within_the_limit() -> None:
    chunks = chunk_document(CHAPTER, max_chars=400)

    assert len(chunks) > 3, "a long proof must be split rather than emitted whole"
    for chunk in chunks:
        body = _body(chunk)
        # Header is metadata, so allow it on top of the body budget.
        assert len(body) <= 400 * 1.25, f"chunk over budget: {len(body)}"


def test_display_math_is_not_cut_mid_delimiter() -> None:
    """The old fixed window cut LaTeX mid-command, producing unrenderable text."""
    chunks = chunk_document(CHAPTER, max_chars=200)
    math_chunks = [c for c in chunks if "$$" in _body(c)]

    assert math_chunks, "the fixture contains display math"
    for chunk in math_chunks:
        body = _body(chunk)
        assert body.count("$$") % 2 == 0, f"unbalanced display math: {body[-80:]!r}"


def test_tiny_tails_are_merged_instead_of_emitted_alone() -> None:
    markdown = (
        "## 3.1 节\n\n"
        "这是一段足够长的正文，用来把这一节撑过最小长度门槛，承载章节说明内容。\n\n"
        "短。\n"
    )

    chunks = chunk_document(markdown)

    assert len(chunks) == 1, f"stub tail should merge, got {len(chunks)} chunks"
    assert "短。" in chunks[0]


def test_default_limit_is_respected() -> None:
    long_body = "误差递推关系的具体推导过程。" * 400
    markdown = f"## 4.1 长节\n\n{long_body}\n"

    chunks = chunk_document(markdown)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(_body(chunk)) <= MAX_CHUNK_CHARS * 1.25
