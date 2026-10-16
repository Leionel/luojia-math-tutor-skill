"""Sampling of textbook content for single-pass LLM note generation.

The sample is the only body text the model sees, so cutting it badly produces a
note that is either thin or fabricated. The previous implementation kept a
proportional prefix of every chunk, which on a real book meant ~56 characters
each — mostly the context header — with LaTeX severed mid-token.
"""

from app.api.routes_notes import _MAX_HEADINGS, _NOTE_CHAR_BUDGET, _sample_chunks


def _chunks(count: int, size: int = 800) -> list[str]:
    return [f"[第 1 章 › 1.{i} 节] 标题 {i}\n" + f"内容{i}。" * (size // 6) for i in range(count)]


def test_small_input_is_returned_whole() -> None:
    chunks = _chunks(3)

    assert _sample_chunks(chunks, char_budget=100_000) == "\n\n".join(chunks)


def test_empty_input_yields_empty_sample() -> None:
    assert _sample_chunks([], char_budget=1000) == ""


def test_sampled_chunks_are_whole_not_prefix_cut() -> None:
    """A severed chunk is worse than no chunk: it reads as source text."""
    chunks = _chunks(200)

    sample = _sample_chunks(chunks, char_budget=8_000)
    sampled_lines = [line for line in sample.splitlines() if line.startswith("内容")]

    assert sampled_lines, "sample must contain body text, not only headers"
    for line in sampled_lines:
        owner = next(c for c in chunks if line in c)
        assert line in owner.splitlines(), f"line was cut mid-chunk: {line[-24:]!r}"


def test_sampling_spans_the_whole_document() -> None:
    total = 200
    chunks = _chunks(total)

    sample = _sample_chunks(chunks, char_budget=8_000)
    picked = sorted(i for i in range(total) if f"标题 {i}\n" in sample)

    assert picked, "nothing was sampled"
    assert picked[0] == 0, "the beginning must be represented"
    assert picked[-1] == total - 1, "the end must be represented"
    assert any(total // 3 <= i <= 2 * total // 3 for i in picked), (
        f"middle third unrepresented: {picked}"
    )

    gaps = [b - a for a, b in zip(picked, picked[1:])]
    assert max(gaps) <= 2 * (total // len(picked)) + 2, f"uneven spacing: {gaps}"


def test_budget_is_respected() -> None:
    chunks = _chunks(400)
    budget = 8_000

    sample = _sample_chunks(chunks, char_budget=budget)

    # Whole chunks cannot be split to hit an exact budget, so allow one chunk of
    # slack — but not the 2x overshoot an off-by-design would produce.
    assert len(sample) <= budget + max(len(c) for c in chunks)


def test_heading_cap_fits_a_real_textbook_outline() -> None:
    """A 150-page textbook has 158 headings; the old cap of 80 hid chapters 4-6."""
    assert _MAX_HEADINGS >= 158


def test_body_budget_exceeds_a_single_chunk_by_a_useful_margin() -> None:
    assert _NOTE_CHAR_BUDGET >= 20_000
