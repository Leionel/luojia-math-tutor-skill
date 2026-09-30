"""Text transforms for the CJK-aware chunk index.

SQLite's default FTS5 tokenizer keeps long CJK runs as single tokens, which
makes BM25 nearly unusable on Chinese textbook prose. The index stores
whitespace-separated CJK bigrams instead, and queries are transformed the
same way before matching.
"""

import re

_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
_TOKEN_RUN = re.compile(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+|[^A-Za-z0-9\u4e00-\u9fff]+")
_INNER_SPACE = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])")
# Function chars whose bigrams add noise but no precision to AND queries.
_FUNCTION = "的了是在和与吗呢吧啊呀么有没里就都把被这个们我你"
# Question scaffolding around a topic word; removed before tokenizing.
_FILLER = [
    "属于哪一节", "是什么意思", "是怎么算", "能讲讲", "没听懂", "听不懂",
    "是什么", "有哪些", "能推出", "哪些", "讲了", "意思", "怎么", "这块",
]
_FILLER_RE = re.compile("|".join(_FILLER))


def cjk_bigram_text(text: str) -> str:
    text = _INNER_SPACE.sub("", text or "")
    parts: list[str] = []
    for run in _TOKEN_RUN.findall(text):
        if _CJK_RUN.fullmatch(run):
            if len(run) == 1:
                parts.append(run)
            else:
                parts.extend(run[i : i + 2] for i in range(len(run) - 1))
        elif run.strip():
            parts.append(run.lower())
    return " ".join(parts)


def cjk_query_groups(query: str, max_groups: int = 12) -> list[list[str]]:
    """One OR-group of bigrams per query topic word.

    Question scaffolding (属于哪一节/是什么/讲了) and single function
    characters are stripped first; an AND query over a full student sentence
    otherwise excludes chunks that lack the filler words.
    """
    cleaned = _FILLER_RE.sub(" ", _INNER_SPACE.sub("", query or ""))
    groups: list[list[str]] = []
    for term in re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+", cleaned):
        if _CJK_RUN.fullmatch(term):
            grams: list[str] = []
            for sub in re.split(f"[{_FUNCTION}]", term):
                if len(sub) >= 2:
                    grams.extend(sub[i : i + 2] for i in range(len(sub) - 1))
                elif len(sub) == 1 and not groups:
                    grams.append(sub)
            if not grams:
                continue
        else:
            grams = [term.lower()]
        unique = sorted(set(grams))
        if unique and unique not in groups:
            groups.append(unique)
        if len(groups) >= max_groups:
            break
    return groups
