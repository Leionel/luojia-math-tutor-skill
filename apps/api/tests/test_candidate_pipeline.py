import pytest
from fastapi.testclient import TestClient

from app.knowledge.candidate_pipeline import build_candidates_from_document, segment_document
from app.main import app
from app.main_deps import get_repository


MARKDOWN = """# 第2章 非线性方程求根

## 2.1 迭代法的基本概念

迭代法是数值分析的核心方法之一。本节介绍不动点迭代的基本思想与收敛性判断。

定义 2.1 不动点：若 f(x*) = x*，则称 x* 为函数 f 的不动点。

## 2.2 牛顿迭代法

牛顿法使用切线代替曲线进行迭代。

定理 2.1（牛顿法局部收敛性）：设 f 在根附近二阶连续可导，则牛顿法局部平方收敛。

证明：由泰勒展开可得……

例 2.1 用牛顿法求方程的根。
"""


def test_segment_document_splits_by_heading_and_type_markers():
    sections = segment_document(MARKDOWN)
    titles = [s.title for s in sections]
    assert any("非线性方程求根" in t for t in titles)
    assert any(t.startswith("定义 2.1") for t in titles)
    assert any("牛顿迭代法" in t for t in titles)

    # 证明 and 例 must attach to the preceding unit, not split new ones.
    theorem_section = next(s for s in sections if s.title.startswith("定理 2.1"))
    assert "泰勒展开" in theorem_section.text
    assert "牛顿法求方程" in theorem_section.text


def test_build_candidates_carries_provenance_and_unclassified_scope():
    proposals = build_candidates_from_document("doc123", "教材.pdf", MARKDOWN)
    assert proposals
    for proposal in proposals:
        assert proposal["candidate_type"] == "new_unit"
        assert proposal["proposed_by"] == "document_pipeline"
        assert proposal["evidence_ref"].startswith("document:doc123:")
        assert proposal["payload"]["scope_level"] == "unclassified"
    # Stable ids so re-uploading the same document dedupes.
    again = build_candidates_from_document("doc123", "教材.pdf", MARKDOWN)
    assert [p["candidate_id"] for p in again] == [p["candidate_id"] for p in proposals]


@pytest.fixture
def client():
    return TestClient(app)


def _expected_ids(document_id: str, markdown: str = MARKDOWN) -> list[str]:
    return [
        p["candidate_id"]
        for p in build_candidates_from_document(document_id, "教材.pdf", markdown)
    ]


def _chapter(number: int) -> str:
    return (
        f"## 2.{number} 迭代法小节 {number}\n\n"
        f"定义 2.{number} 收敛阶：设迭代格式为 x_(k+1) = g(x_k)，若存在常数 c 与 p，"
        f"使得误差满足 e_(k+1) ≈ c·e_k^p，则称该迭代为 p 阶收敛，c 为渐进误差常数。"
        f"这一小节的文字用于把文档撑到跨越多个分块窗口。\n"
    )


# Long enough that chunk_markdown(500, 50) produces several overlapping chunks.
LONG_MARKDOWN = "# 第2章 非线性方程求根\n\n" + "".join(_chapter(n) for n in range(1, 9))


def test_candidates_from_document_route(client):
    repo = get_repository()
    document_id = repo.insert_document("pipeline_sample.pdf", "demo-user", MARKDOWN)
    repo.insert_document_chunks(document_id, ["## 2.2 牛顿迭代法\n牛顿法使用切线代替曲线。"])
    expected = _expected_ids(document_id)
    try:
        res = client.post(
            "/api/courses/numerical_analysis/candidates/from-document",
            json={"document_id": document_id},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "created"
        assert data["total"] == len(expected)
        assert [c["candidate_id"] for c in data["candidates"]] == expected
        assert all(c["status"] == "pending" for c in data["candidates"])
        assert all(c["payload"]["scope_level"] == "unclassified" for c in data["candidates"])

        listing = client.get(
            "/api/courses/numerical_analysis/candidates?status=pending"
        ).json()
        candidate_ids = [c["candidate_id"] for c in listing["candidates"]]
        assert candidate_ids.count(data["candidates"][0]["candidate_id"]) == 1

        # Re-running the same document increments support instead of duplicating.
        rerun = client.post(
            "/api/courses/numerical_analysis/candidates/from-document",
            json={"document_id": document_id},
        ).json()
        assert [c["candidate_id"] for c in rerun["candidates"]] == expected
        assert all(c["support_count"] == 2 for c in rerun["candidates"])
    finally:
        with repo.connect() as conn:
            conn.execute(
                "delete from document_chunks where document_id = ?", (document_id,)
            )
            conn.execute("delete from documents where id = ?", (document_id,))


def test_overlapping_chunks_do_not_change_candidates(client):
    """Regression: candidates used to be rebuilt by re-joining overlapping chunks.

    `chunk_markdown` overlaps by 50 chars, so `"\\n".join(chunks)` duplicated
    text at every boundary. That inflated section content and produced repeated
    candidate ids, which made `support_count` read 2 after a single upload.
    """
    from app.api.routes_uploads import chunk_markdown

    repo = get_repository()
    document_id = repo.insert_document("overlap.pdf", "demo-user", LONG_MARKDOWN)
    repo.insert_document_chunks(document_id, chunk_markdown(LONG_MARKDOWN))
    try:
        chunks = repo.list_document_chunks(document_id)
        assert len(chunks) > 1, "sample must span multiple chunks to be meaningful"
        assert len("\n".join(chunks)) > len(LONG_MARKDOWN), "overlap must be present"

        data = client.post(
            "/api/courses/numerical_analysis/candidates/from-document",
            json={"document_id": document_id},
        ).json()

        ids = [c["candidate_id"] for c in data["candidates"]]
        assert ids == _expected_ids(document_id, LONG_MARKDOWN)
        assert len(set(ids)) == len(ids), "one upload must not repeat a candidate id"
        assert all(c["support_count"] == 1 for c in data["candidates"])
        for candidate in data["candidates"]:
            content = candidate["payload"]["content"]
            assert content in LONG_MARKDOWN, "candidate content must come from the source text"
    finally:
        with repo.connect() as conn:
            conn.execute(
                "delete from document_chunks where document_id = ?", (document_id,)
            )
            conn.execute("delete from documents where id = ?", (document_id,))


def test_candidates_from_document_requires_stored_markdown(client):
    """Fail closed rather than reconstructing a lossy document from chunks."""
    repo = get_repository()
    document_id = repo.insert_document("legacy.pdf", "demo-user")
    repo.insert_document_chunks(document_id, ["定义 2.1 不动点：若 f(x*) = x*，则称 x* 为不动点。"])
    try:
        res = client.post(
            "/api/courses/numerical_analysis/candidates/from-document",
            json={"document_id": document_id},
        )
        assert res.status_code == 409
        assert "原文" in res.json()["detail"]
    finally:
        with repo.connect() as conn:
            conn.execute(
                "delete from document_chunks where document_id = ?", (document_id,)
            )
            conn.execute("delete from documents where id = ?", (document_id,))


def test_duplicate_headings_do_not_collapse_into_one_candidate():
    """Two sections sharing a heading must stay two candidates."""
    repeated = (
        "# 第3章 插值法\n\n"
        "定义 3.1 拉格朗日插值：在互异节点上构造次数不超过 n 的多项式，"
        "使其在每个节点取给定的函数值，这样的多项式存在且唯一。\n\n"
        "定义 3.1 拉格朗日插值：另一种等价的表述方式是使用基函数的线性组合，"
        "每个基函数在自己的节点取一、在其余节点取零，从而直接满足插值条件。\n"
    )
    proposals = build_candidates_from_document("doc-dup", "dup.pdf", repeated)
    ids = [p["candidate_id"] for p in proposals]

    assert len(proposals) == 2
    assert len(set(ids)) == 2, "identical titles must not share a candidate id"
    assert proposals[0]["payload"]["content"] != proposals[1]["payload"]["content"]


# Shaped like real MinerU output, which renders textbook markers as headings.
MINERU_SHAPED = """## 第 1 章 基础知识

本章介绍误差来源与浮点数系统，这些内容是后续所有数值算法分析的共同基础。

## 定义 1.1

设 f 在区间 [a,b] 上连续，若存在 x* 属于 [a,b] 使得 f(x*)=0，则称 x* 为 f 的一个零点。

## 定理 2.1（介值定理）

若 f 在 [a,b] 上连续且 f(a)·f(b)<0，则至少存在一点 ξ 属于 (a,b) 使得 f(ξ)=0。

证明 由连续函数在闭区间上取得端点之间一切值可知，特别地会取得零值，证毕。

## 算法 2.1 二分法

步骤一：取区间中点；步骤二：判断中点处函数符号；步骤三：保留异号半区间并重复。
"""


def test_mineru_style_heading_markers_keep_their_unit_type():
    """`## 定义 1.1` is both a heading and a marker; the marker must win."""
    sections = segment_document(MINERU_SHAPED)
    by_title = {s.title: s.unit_type for s in sections}

    assert by_title["定义 1.1"] == "definition"
    assert by_title["定理 2.1（介值定理）"] == "theorem"
    assert by_title["算法 2.1 二分法"] == "algorithm"
    assert by_title["第 1 章 基础知识"] == "concept"

    # 证明 still attaches to the theorem instead of starting its own unit.
    theorem = next(s for s in sections if s.unit_type == "theorem")
    assert "取得零值" in theorem.text
    assert not any(s.title.startswith("证明") for s in sections)


def test_candidates_from_mineru_style_markdown_carry_types():
    proposals = build_candidates_from_document("doc-md", "book.pdf", MINERU_SHAPED)
    types = {p["payload"]["title"]: p["payload"]["type"] for p in proposals}

    assert types["定义 1.1"] == "definition"
    assert types["定理 2.1（介值定理）"] == "theorem"
    assert types["算法 2.1 二分法"] == "algorithm"


def test_candidates_from_document_requires_existing_document(client):
    res = client.post(
        "/api/courses/numerical_analysis/candidates/from-document",
        json={"document_id": "doc_missing"},
    )
    assert res.status_code == 404
