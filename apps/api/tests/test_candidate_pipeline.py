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


def test_candidates_from_document_route(client):
    repo = get_repository()
    document_id = repo.insert_document("pipeline_sample.pdf", "demo-user")
    repo.insert_document_chunks(
        document_id,
        [
            "## 2.2 牛顿迭代法\n牛顿法使用切线代替曲线进行迭代，通过切线斜率逐步逼近方程的根。",
            "定义 2.1 不动点：若 f(x*) = x*，则称 x* 为函数 f 的不动点，迭代法围绕不动点的存在性与收敛性展开。",
        ],
    )
    try:
        res = client.post(
            "/api/courses/numerical_analysis/candidates/from-document",
            json={"document_id": document_id},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "created"
        assert data["total"] == 2
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
        rerun_ids = [c["candidate_id"] for c in rerun["candidates"]]
        assert rerun_ids == candidate_ids[: len(rerun_ids)]
        assert all(c["support_count"] == 2 for c in rerun["candidates"])
    finally:
        with repo.connect() as conn:
            conn.execute(
                "delete from document_chunks where document_id = ?", (document_id,)
            )
            conn.execute("delete from documents where id = ?", (document_id,))


def test_candidates_from_document_requires_existing_document(client):
    res = client.post(
        "/api/courses/numerical_analysis/candidates/from-document",
        json={"document_id": "doc_missing"},
    )
    assert res.status_code == 404
