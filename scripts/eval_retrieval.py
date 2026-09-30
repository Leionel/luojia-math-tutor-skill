"""Real retrieval evaluation over the ingested textbook chunks.

Three arms are compared on the same gold set:

- bm25:   the CJK-bigram FTS index used by the production read path
- vector: text-embedding-v3 cosine similarity (chunk vectors cached on disk)
- hybrid: reciprocal-rank fusion of the two, mirroring fast_context

Gold chunks are resolved from the deterministic segmentation itself: a chunk
is gold when the case's expected marker appears at a heading position (strict)
or anywhere (loose fallback) inside the expected section.
"""

import asyncio
import hashlib
import json
import re
import sqlite3
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "apps" / "api"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / "apps" / "api" / ".env")

from app.memory.text_index import cjk_query_groups  # noqa: E402

DB_PATH = ROOT / "apps" / "api" / "luojia_tutor.db"
EVAL_PATH = ROOT / "evaluation" / "retrieval_eval.json"
RESULTS_DIR = ROOT / "results"
EMBED_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
EMBED_MODEL = "text-embedding-v3"
TOP_K = 20
RRF_K = 60


def norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def load_chunks() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "select rowid, document_id, content from document_chunks order by rowid"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def resolve_gold(case: dict, chunks: list[dict], norms: list[str]) -> list[int]:
    markers = [norm(case["expected_marker"]), norm(case.get("subject_marker") or "")]
    section = norm(case["expected_section"])
    strict: list[int] = []
    loose: list[int] = []
    for chunk, n in zip(chunks, norms):
        if section and section not in n:
            continue
        for marker in markers:
            if not marker or marker not in n:
                continue
            loose.append(chunk["rowid"])
            if f"##{marker}" in n or n.startswith(marker):
                strict.append(chunk["rowid"])
    return strict or loose


def bm25_rank(query: str, document_id: str, conn: sqlite3.Connection) -> list[int]:
    groups = cjk_query_groups(query)
    if not groups:
        return []
    match = " AND ".join(
        "(" + " OR ".join(f'"{gram}"' for gram in group) + ")" for group in groups
    )
    try:
        rows = conn.execute(
            """
            select idx.chunk_rowid as rowid
            from document_chunks_index idx
            join document_chunks dc on dc.rowid = idx.chunk_rowid
            where dc.document_id = ? and document_chunks_index match ?
            order by bm25(document_chunks_index)
            limit ?
            """,
            (document_id, match, TOP_K),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [row[0] for row in rows]


async def embed_batch(
    client: httpx.AsyncClient, api_key: str, texts: list[str]
) -> list[list[float]]:
    response = await client.post(
        EMBED_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": EMBED_MODEL, "input": texts},
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()["data"]
    data.sort(key=lambda item: item["index"])
    return [item["embedding"] for item in data]


async def embed_all(
    texts: list[str], api_key: str, cache_path: Path, batch_size: int = 16
) -> list[list[float]]:
    cache: dict[str, list[float]] = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    keys = [hashlib.md5(text.encode("utf-8")).hexdigest() for text in texts]
    positions: dict[str, list[int]] = defaultdict(list)
    for idx, key in enumerate(keys):
        positions[key].append(idx)

    vectors: list[list[float] | None] = [
        cache.get(key) for key in keys
    ]
    missing = [key for key in positions if key not in cache]
    text_by_key = {key: texts[positions[key][0]] for key in positions}

    async with httpx.AsyncClient() as client:
        for start in range(0, len(missing), batch_size):
            batch_keys = missing[start : start + batch_size]
            try:
                embeddings = await embed_batch(
                    client, api_key, [text_by_key[key] for key in batch_keys]
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  embed batch failed ({exc}); arm degrades for {len(batch_keys)} texts")
                continue
            for key, vec in zip(batch_keys, embeddings):
                cache[key] = vec
                for idx in positions[key]:
                    vectors[idx] = vec
    cache_path.write_text(json.dumps(cache), encoding="utf-8")
    return [v or [] for v in vectors]


def cosine_ranks(
    query_vecs: list[list[float]], chunk_vecs: list[list[float]], top_k: int = TOP_K
) -> dict[int, list[int]]:
    try:
        import numpy as np
    except ImportError:
        np = None

    ranks: dict[int, list[int]] = {}
    if np is not None:
        cmat = np.array([v for v in chunk_vecs if v], dtype=np.float32) if any(chunk_vecs) else None
        keep = [i for i, v in enumerate(chunk_vecs) if v]
        if cmat is not None and len(cmat):
            cmat = cmat / np.linalg.norm(cmat, axis=1, keepdims=True).clip(min=1e-9)
            for qi, qv in enumerate(query_vecs):
                if not qv:
                    ranks[qi] = []
                    continue
                q = np.array(qv, dtype=np.float32)
                q = q / max(float(np.linalg.norm(q)), 1e-9)
                scores = cmat @ q
                top = np.argsort(-scores)[:top_k]
                ranks[qi] = [chunks_rowids[keep[i]] for i in top]
        else:
            for qi in range(len(query_vecs)):
                ranks[qi] = []
        return ranks

    def dot(a: list[float], b: list[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    norms_c = [max(dot(v, v), 1e-9) ** 0.5 for v in chunk_vecs]
    for qi, qv in enumerate(query_vecs):
        if not qv:
            ranks[qi] = []
            continue
        nq = max(dot(qv, qv), 1e-9) ** 0.5
        scored = sorted(
            (
                (dot(qv, cv) / (nq * nc), ci)
                for ci, (cv, nc) in enumerate(zip(chunk_vecs, norms_c))
                if cv
            ),
            reverse=True,
        )
        ranks[qi] = [chunks_rowids[ci] for _, ci in scored[:top_k]]
    return ranks


def rrf_fuse(a: list[int], b: list[int]) -> list[int]:
    scores: dict[int, float] = defaultdict(float)
    for rank, rowid in enumerate(a):
        scores[rowid] += 1.0 / (RRF_K + rank + 1)
    for rank, rowid in enumerate(b):
        scores[rowid] += 1.0 / (RRF_K + rank + 1)
    return [rowid for rowid, _ in sorted(scores.items(), key=lambda kv: -kv[1])][:TOP_K]


def metrics(golds: list[set[int]], rankings: list[list[int]]) -> dict[str, float]:
    out = {"recall@3": 0.0, "recall@5": 0.0, "mrr@10": 0.0}
    n = len(golds)
    if n == 0:
        return out
    for gold, ranking in zip(golds, rankings):
        for k in (3, 5):
            out[f"recall@{k}"] += len(gold & set(ranking[:k])) / len(gold)
        mrr = 0.0
        for rank, rowid in enumerate(ranking[:10], start=1):
            if rowid in gold:
                mrr = 1.0 / rank
                break
        out["mrr@10"] += mrr
    return {key: round(value / n, 4) for key, value in out.items()}


chunks_rowids: list[int] = []


async def main() -> None:
    import os

    api_key = os.getenv("LLM_API_KEY", "")
    cases = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    chunks = load_chunks()
    global chunks_rowids
    chunks_rowids = [c["rowid"] for c in chunks]
    norms = [norm(c["content"]) for c in chunks]
    conn = sqlite3.connect(DB_PATH)

    print(f"chunks={len(chunks)} cases={len(cases)}")
    golds: list[set[int]] = []
    unresolved = 0
    for case in cases:
        gold = set(resolve_gold(case, chunks, norms))
        if not gold:
            unresolved += 1
        golds.append(gold)
    print(f"gold resolved for {len(cases) - unresolved}/{len(cases)} cases")

    bm25_ranks = [bm25_rank(case["query"], case["source_document_id"], conn) for case in cases]

    print("embedding chunks + queries (text-embedding-v3)...")
    started = time.perf_counter()
    chunk_vecs = await embed_all([c["content"] for c in chunks], api_key, RESULTS_DIR / "chunk_embeddings.json")
    query_vecs = await embed_all([case["query"] for case in cases], api_key, RESULTS_DIR / "query_embeddings.json")
    print(f"  embeddings done in {time.perf_counter() - started:.1f}s")

    pos_of = {rowid: idx for idx, rowid in enumerate(chunks_rowids)}
    vec_ranks_idx = cosine_ranks(query_vecs, chunk_vecs)
    vec_ranks = [vec_ranks_idx[i] for i in range(len(cases))]

    arms = {
        "bm25": bm25_ranks,
        "vector": vec_ranks,
        "hybrid": [rrf_fuse(a, b) for a, b in zip(bm25_ranks, vec_ranks)],
    }

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "chunks": len(chunks),
        "cases": len(cases),
        "gold_unresolved": unresolved,
        "overall": {},
        "by_style": {},
    }
    print(f"\n{'config':<8} {'recall@3':>9} {'recall@5':>9} {'mrr@10':>8}")
    for name, ranks in arms.items():
        overall = metrics(golds, ranks)
        report["overall"][name] = overall
        print(f"{name:<8} {overall['recall@3']:>9.4f} {overall['recall@5']:>9.4f} {overall['mrr@10']:>8.4f}")

    styles = sorted({case["style"] for case in cases})
    for style in styles:
        idx = [i for i, case in enumerate(cases) if case["style"] == style]
        report["by_style"][style] = {
            name: metrics([golds[i] for i in idx], [arms[name][i] for i in idx])
            for name in arms
        }

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "retrieval_eval_results.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
