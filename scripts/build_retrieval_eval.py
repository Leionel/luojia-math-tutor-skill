"""Build a retrieval evaluation set from the approved textbook graph.

Queries are derived from the deterministic segmentation itself (unit titles,
in-content terminology, and typed relations), so ground truth needs no manual
labelling and survives re-chunking: every case carries the unit id plus the
marker/section text a runner can resolve against whatever chunks exist.
"""

import argparse
import json
import random
import re
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STOP_TERMS = {
    "定义", "定理", "算法", "引理", "推论", "证明", "注", "例", "例题",
    "如下", "下列", "由此", "因此", "其中", "则称", "称为", "叫做", "记为",
    "方法", "公式", "条件", "性质", "结论", "问题", "内容", "方式", "情形",
}
NOISE_TITLE = re.compile(r"(练习|习题|复习|思考题|参考文献|索引|封面|目录|前言|附录)")
MARKER_ONLY = re.compile(r"^\s*(定义|定理|算法|引理|推论|证明|注|例题|例|命题)\s*[\d.]+\s*$")
NUMBER_PREFIX = re.compile(r"^\s*(?:第\s*\d+\s*章|[Kk])?\s*\d+(?:\.\d+)*\s+")
LATEX_BLOCK = re.compile(r"\$\$[\s\S]*?\$\$")
LATEX_INLINE = re.compile(r"\$[^$]*\$")
MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
TERM_PATTERNS = [
    re.compile(r"(?:称为|叫做|称作|记为|记作|称之为)\s*([\u4e00-\u9fa5A-Za-z]{2,10})"),
    re.compile(r"称为\s*([\u4e00-\u9fa5]{2,10})"),
]


def plain(text: str) -> str:
    text = MD_IMAGE.sub(" ", text or "")
    text = LATEX_BLOCK.sub(" ◇ ", text)
    text = LATEX_INLINE.sub("◇", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"[{}^_&\s]+", " ", text)
    return text.strip()


def clean_title(title: str) -> str:
    name = NUMBER_PREFIX.sub("", title).strip()
    name = re.sub(r"^\s*[(（]\s*\d+\s*[)）]\s*", "", name)
    return (name.strip().rstrip("。.") or title.strip())


def extract_terms(content: str) -> list[str]:
    text = plain(content)
    terms: list[str] = []
    for pattern in TERM_PATTERNS:
        for match in pattern.finditer(text):
            term = re.sub(r"[A-Za-z0-9]+$", "", match.group(1).strip("，。；：、的"))
            if len(term) < 2 or term in STOP_TERMS:
                continue
            if not re.search(r"[一-鿿]", term):
                continue
            if term not in terms:
                terms.append(term)
    return terms[:3]


def short_name(title: str) -> str:
    # "定理 2.1（介值定理）" is best asked by its name, not its number.
    named = re.search(r"[（(]\s*([^）)]{2,14})\s*[）)]", title)
    if named and re.search(r"[一-鿿A-Za-z]", named.group(1)):
        return named.group(1).strip()
    name = clean_title(title)
    name = re.split(r"[，。；：（(]", name)[0].strip()
    return name[:20]


def usable_name(name: str) -> bool:
    if len(name) < 3 or name in STOP_TERMS or MARKER_ONLY.match(name):
        return False
    if re.fullmatch(r"[A-Za-z]+\s*[\d.]+", name) or re.fullmatch(r"[\d.]+", name):
        return False
    # Proof/example labels carry no topic of their own.
    return not re.match(r"^(证明|注|例题|例|命题)\s*[\d.]*$", name)


def is_sentence_fragment(name: str) -> bool:
    return bool(re.search(r"(考虑|可知|验证|如下|设|令|求)", name))





def load_units(db: Path) -> list[dict]:
    conn = sqlite3.connect(db)
    rows = [json.loads(raw) for (raw,) in conn.execute("select data from graph_candidates")]
    conn.close()
    units = []
    for row in rows:
        if row.get("candidate_type") != "new_unit" or row.get("status") != "pending":
            continue
        payload = row["payload"]
        title = (payload.get("title") or "").strip()
        if not title or NOISE_TITLE.search(title):
            continue
        units.append(payload)
    return units


def load_relations(db: Path) -> list[dict]:
    conn = sqlite3.connect(db)
    rows = [json.loads(raw) for (raw,) in conn.execute("select data from graph_candidates")]
    conn.close()
    return [
        row["payload"]
        for row in rows
        if row.get("candidate_type") == "new_relation" and row.get("status") == "pending"
    ]


def build_cases(units: list[dict], relations: list[dict]) -> list[dict]:
    by_id = {u["id"]: u for u in units}
    cases: list[dict] = []
    seen: set[str] = set()

    def add(query: str, style: str, expected: list[str], payload: dict, extra_marker: str = "") -> None:
        query = re.sub(r"\s+", " ", query).strip()
        key = query.lower()
        if len(query) < 4 or key in seen or not expected:
            return
        seen.add(key)
        cases.append(
            {
                "id": f"rev_{len(cases) + 1:04d}",
                "query": query,
                "style": style,
                "expected_unit_ids": expected,
                "expected_marker": payload.get("title"),
                "subject_marker": extra_marker or "",
                "expected_section": (payload.get("chapter_path") or [])[-1] if payload.get("chapter_path") else "",
                "source_document_id": payload.get("source_document_id"),
                "difficulty": payload.get("difficulty", 3),
            }
        )

    for unit in units:
        title = unit["title"]
        named = clean_title(title)
        marker_only = bool(MARKER_ONLY.match(title))
        section = (unit.get("chapter_path") or [])[-1] if unit.get("chapter_path") else ""
        section_name = clean_title(section) if section else ""

        # A. the concept name itself
        if not marker_only and len(named) >= 2:
            add(named, "title", [unit["id"]], unit)
        else:
            named_marker = short_name(title)
            if usable_name(named_marker) and not is_sentence_fragment(named_marker):
                add(named_marker, "title", [unit["id"]], unit)

        # B. terminology the unit itself defines
        terms = extract_terms(unit.get("content", ""))
        for term in terms[:2]:
            add(f"什么是{term}？", "definition", [unit["id"]], unit)
        if terms:
            procedural = re.search(r"(法|公式|算法|迭代|逼近|插值|求积|矩阵|多项式|常数|误差)", terms[0])
            if procedural:
                add(f"{terms[0]}是怎么算的？", "howto", [unit["id"]], unit)
            else:
                add(f"{terms[0]}是什么意思？", "howto", [unit["id"]], unit)

        # C. marker inside its section, for numbered definitions/theorems
        if marker_only and section_name:
            add(f"{section_name}里的{title.strip()}讲了什么？", "scoped_marker", [unit["id"]], unit)

        # D. colloquial paraphrase of a named concept
        spoken = short_name(title)
        if usable_name(spoken) and not is_sentence_fragment(spoken):
            if len(spoken) >= 3 and random.Random(unit["id"]).random() < 0.35:
                add(f"{spoken}这块我没听懂，能讲讲吗", "colloquial", [unit["id"]], unit)

    # E. hierarchy questions resolved through part_of relations
    for rel in relations:
        source = by_id.get(rel.get("source_unit_id"))
        target = by_id.get(rel.get("target_unit_id"))
        if not source or not target:
            continue
        if rel.get("relation_type") == "part_of":
            name = short_name(source["title"])
            if not usable_name(name) or is_sentence_fragment(name):
                continue
            add(f"{name}属于哪一节？", "hierarchy", [rel["target_unit_id"]], target, extra_marker=source["title"])
        # F. typed relations: ask from whichever side actually carries a name
        elif rel.get("relation_type") in {"derives_from", "example_of"}:
            a, b = short_name(source["title"]), short_name(target["title"])
            a_ok = usable_name(a) and not is_sentence_fragment(a)
            b_ok = usable_name(b) and not is_sentence_fragment(b)
            if not a_ok and not b_ok:
                continue
            if rel.get("relation_type") == "example_of":
                subject = b if b_ok else a
                add(f"{subject}有哪些例题？", "relation", [source["id"], target["id"]], target, extra_marker=source["title"])
            else:
                subject = b if b_ok else a
                add(f"{subject}能推出哪些结论？", "relation", [source["id"], target["id"]], target, extra_marker=source["title"])

    return cases


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=str(ROOT / "apps/api/data/course_store.db"))
    parser.add_argument("--out", default=str(ROOT / "evaluation/retrieval_eval.json"))
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    random.seed(args.seed)
    units = load_units(Path(args.db))
    relations = load_relations(Path(args.db))
    cases = build_cases(units, relations)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    styles = Counter(c["style"] for c in cases)
    chapters = Counter((c["expected_section"] or "?").split(" ")[0] for c in cases)
    print(f"units={len(units)} relations={len(relations)} cases={len(cases)}")
    print("by style:  " + ", ".join(f"{k}={v}" for k, v in sorted(styles.items())))
    print("by chapter:" + ", ".join(f"{k}={v}" for k, v in sorted(chapters.items())))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
