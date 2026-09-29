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


def _units(proposals):
    return [p for p in proposals if p["candidate_type"] == "new_unit"]


def _relations(proposals):
    return [p for p in proposals if p["candidate_type"] == "new_relation"]


def test_segment_document_splits_by_heading_and_type_markers():
    sections = segment_document(MARKDOWN)
    titles = [s.title for s in sections]
    assert any("非线性方程求根" in t for t in titles)
    assert any(t.startswith("定义 2.1") for t in titles)
    assert any("牛顿迭代法" in t for t in titles)

    # 证明 and 例 are their own units now; the link to the theorem is a typed
    # relation, not string concatenation inside one blob.
    by_type = {s.unit_type for s in sections}
    assert "proof" in by_type
    assert "example" in by_type

    theorem_section = next(s for s in sections if s.title.startswith("定理 2.1"))
    assert "泰勒展开" not in theorem_section.text
    proof_section = next(s for s in sections if s.unit_type == "proof")
    assert "泰勒展开" in proof_section.text
    assert proof_section.anchor_order == theorem_section.order


def test_build_candidates_carries_provenance_and_unclassified_scope():
    proposals = build_candidates_from_document("doc123", "教材.pdf", MARKDOWN)
    assert proposals
    for proposal in proposals:
        assert proposal["proposed_by"] == "document_pipeline"
        assert proposal["evidence_ref"].startswith("document:doc123:")
    for unit in _units(proposals):
        assert unit["payload"]["scope_level"] == "unclassified"
    for relation in _relations(proposals):
        payload = relation["payload"]
        assert payload["source_unit_id"] != payload["target_unit_id"]
        assert 0 < payload["confidence"] <= 1
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
        units = [c for c in data["candidates"] if c["candidate_type"] == "new_unit"]
        relations = [c for c in data["candidates"] if c["candidate_type"] == "new_relation"]
        assert units and relations, "textbook markdown must yield units and typed relations"
        assert all(c["payload"]["scope_level"] == "unclassified" for c in units)
        for relation in relations:
            payload = relation["payload"]
            assert payload["relation_type"] in {
                "supports_proof",
                "example_of",
                "derives_from",
                "part_of",
            }
            assert payload["source_unit_id"] != payload["target_unit_id"]

        listing = client.get(
            "/api/courses/numerical_analysis/candidates?status=pending"
        ).json()
        candidate_ids = [c["candidate_id"] for c in listing["candidates"]]
        assert candidate_ids.count(data["candidates"][0]["candidate_id"]) == 1

        # Re-running the same document must not create duplicates, and must not
        # inflate support_count: it is the same source, not a second one.
        rerun = client.post(
            "/api/courses/numerical_analysis/candidates/from-document",
            json={"document_id": document_id},
        ).json()
        assert [c["candidate_id"] for c in rerun["candidates"]] == expected
        assert all(c["support_count"] == 1 for c in rerun["candidates"])
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
    The old fixed-window chunker (500 chars, 50 overlap) is gone from
    production code; reproduce it here because the regression is about what
    overlapping chunks did to candidate extraction.
    """

    def overlapping_chunks(text: str, size: int = 500, overlap: int = 50) -> list[str]:
        out, start = [], 0
        while start < len(text):
            out.append(text[start:start + size])
            start += size - overlap
        return out

    repo = get_repository()
    document_id = repo.insert_document("overlap.pdf", "demo-user", LONG_MARKDOWN)
    repo.insert_document_chunks(document_id, overlapping_chunks(LONG_MARKDOWN))
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

    # 证明 is its own unit now, anchored to the theorem it supports.
    theorem = next(s for s in sections if s.unit_type == "theorem")
    assert "取得零值" not in theorem.text
    proof = next(s for s in sections if s.unit_type == "proof")
    assert "取得零值" in proof.text
    assert proof.anchor_order == theorem.order


def test_candidates_from_mineru_style_markdown_carry_types():
    proposals = build_candidates_from_document("doc-md", "book.pdf", MINERU_SHAPED)
    types = {p["payload"]["title"]: p["payload"]["type"] for p in _units(proposals)}

    assert types["定义 1.1"] == "definition"
    assert types["定理 2.1（介值定理）"] == "theorem"
    assert types["算法 2.1 二分法"] == "algorithm"


def test_relations_link_proof_and_example_to_their_anchor():
    markdown = (
        "## 2.2 牛顿迭代法\n\n"
        "本节介绍牛顿法的基本思想与收敛性质，这些内容是后续误差分析的共同基础。\n\n"
        "定理 2.2 局部收敛性：设 f 二阶连续可微且 f'(x*) 不为零，则牛顿法局部二阶收敛。\n\n"
        "证明 由泰勒展开代入迭代格式，保留主导项即得误差递推关系，故收敛性成立。\n\n"
        "例 2.1 取 f(x)=x²-2，从 x0=1 出发迭代三步即得 1.41421356，与精确值吻合。\n\n"
        "推论 2.1 若初值足够接近单根，则误差平方级递减，这由上述定理直接推出。\n"
    )

    proposals = build_candidates_from_document("doc-rel", "book.pdf", markdown)
    units = {p["payload"]["id"]: p["payload"]["type"] for p in _units(proposals)}
    edges = {
        (units[p["payload"]["source_unit_id"]], p["payload"]["relation_type"])
        for p in _relations(proposals)
    }

    assert ("proof", "supports_proof") in edges
    assert ("example", "example_of") in edges
    assert ("corollary", "derives_from") in edges
    for relation in _relations(proposals):
        payload = relation["payload"]
        assert payload["source_unit_id"] in units
        assert payload["target_unit_id"] in units


def test_part_of_links_atoms_to_their_section():
    proposals = build_candidates_from_document("doc-md", "book.pdf", MINERU_SHAPED)
    units = {p["payload"]["id"]: p["payload"]["title"] for p in _units(proposals)}
    part_of = [
        (units[p["payload"]["source_unit_id"]], units[p["payload"]["target_unit_id"]])
        for p in _relations(proposals)
        if p["payload"]["relation_type"] == "part_of"
    ]

    assert part_of, "atoms must carry the hierarchy small-to-big retrieval expands along"
    assert all(source != target for source, target in part_of)


def test_atoms_carry_their_chapter_path():
    markdown = (
        "# 第 2 章 非线性方程\n\n"
        "## 2.4 牛顿法\n\n"
        "本节讨论牛顿法及其收敛性质，这些内容是后续误差分析的共同基础。\n\n"
        "定理 2.4 局部二次收敛性：设 f 二阶连续可微，则牛顿法局部二阶收敛。\n\n"
        "### 2.4.1 收敛阶补充\n\n"
        "定义 2.5 收敛阶：若误差满足 e_(k+1) ≈ c·e_k^p，则称为 p 阶收敛。\n"
    )

    units = [p["payload"] for p in _units(build_candidates_from_document("doc-path", "book.pdf", markdown))]
    theorem = next(p for p in units if p["type"] == "theorem")
    definition = next(p for p in units if p["type"] == "definition")

    assert theorem["chapter_path"] == ["第 2 章 非线性方程", "2.4 牛顿法"]
    assert theorem["context_header"] == "第 2 章 非线性方程 › 2.4 牛顿法"
    assert theorem["source_document_id"] == "doc-path"
    assert definition["chapter_path"] == [
        "第 2 章 非线性方程",
        "2.4 牛顿法",
        "2.4.1 收敛阶补充",
    ]


def test_hierarchy_is_recovered_when_markdown_levels_are_flat() -> None:
    """MinerU emitted all 158 headings of a real textbook as `##`.

    The '#' count then carries no hierarchy, so depth must come from the
    section numbering; otherwise every atom's chapter path collapses to just
    its nearest heading.
    """
    markdown = (
        "## 第 2 章 非线性方程\n\n"
        "## 2.1 单个方程求解问题\n\n"
        "## 2.1.3 Newton 法\n\n"
        "定理 2.4 局部二次收敛性：设 f 二阶连续可微，则牛顿法局部二阶收敛。\n"
    )

    sections = [s for s in segment_document(markdown) if s.unit_type == "theorem"]

    assert sections[0].chapter_path == [
        "第 2 章 非线性方程",
        "2.1 单个方程求解问题",
        "2.1.3 Newton 法",
    ]


def test_a_new_section_clears_deeper_heading_levels():
    """An atom must not inherit a stale subsection after the section changes."""
    markdown = (
        "# 第 3 章 插值法\n\n"
        "## 3.1 第一节\n\n"
        "### 3.1.1 小节\n\n"
        "定义 3.1 甲：内容足够长以通过最小长度过滤，用于承载第一个小节的说明。\n\n"
        "## 3.2 第二节\n\n"
        "定义 3.2 乙：内容足够长以通过最小长度过滤，用于承载第二个小节的说明。\n"
    )

    definitions = [s for s in segment_document(markdown) if s.unit_type == "definition"]

    assert definitions[0].chapter_path == ["第 3 章 插值法", "3.1 第一节", "3.1.1 小节"]
    assert definitions[1].chapter_path == ["第 3 章 插值法", "3.2 第二节"]


FRONT_MATTER_MARKDOWN = """## Numerical Analysis

时间：August 24, 2022。组织：数学与统计学院。这是一段扉页说明文字，长度足以通过最小长度过滤。

## 前言

本书是在讲义基础上整理而成的，全书共分为六章，第一章介绍误差来源与浮点数系统等基础知识。

## 目录

1.1 数值分析的对象和特点 . 1
1.2 数值计算的误差 . 5

## 第 1 章 基础知识

本章介绍数值分析的对象、特点与误差来源，这些内容是后续所有算法分析的共同基础。

## 1.1 数值分析的对象和特点

数值分析研究数值计算方法，本节给出课程的整体框架与学习要求，内容足够长以通过过滤。

定义 1.1 近似值：设 x 为准确值，x* 为其近似，则称 e = x - x* 为误差。
"""


def test_front_matter_is_not_promoted_to_knowledge_units():
    """Title page, 前言 and 目录 sit outside the numbered outline."""
    proposals = build_candidates_from_document("doc-front", "book.pdf", FRONT_MATTER_MARKDOWN)
    titles = {p["payload"]["title"] for p in _units(proposals)}

    assert "Numerical Analysis" not in titles
    assert "前言" not in titles
    assert "目录" not in titles
    # Chapter and numbered-section introductions are real teaching content.
    assert "第 1 章 基础知识" in titles
    assert any(t.startswith("定义 1.1") for t in titles)


def test_front_matter_filter_ignores_typed_markers():
    """A definition is never front matter, even before chapter 1."""
    markdown = (
        "## 前言\n\n"
        "本书在讲义基础上整理而成，篇幅足够通过最小长度过滤，用于承载前置说明。\n\n"
        "定义 0.1 近似值：设 x 为准确值，x* 为其近似值，则称 e = x - x* 为误差。\n"
    )

    units = _units(build_candidates_from_document("doc-fm2", "b.pdf", markdown))
    types = {p["payload"]["type"] for p in units}

    assert "definition" in types
    assert not any(p["payload"]["title"] == "前言" for p in units)


def test_back_matter_is_dropped_even_after_the_last_chapter():
    """参考文献 inherits the last chapter's path unless the outline is reset."""
    markdown = (
        "## 第 6 章 常微分方程\n\n"
        "本章介绍常微分方程的数值解法，这些内容是全书的收尾部分，篇幅足够通过过滤。\n\n"
        "## 6.1 欧拉方法\n\n"
        "欧拉方法是最简单的单步法，本节给出其构造与收敛性，篇幅足够通过最小长度过滤。\n\n"
        "## 参考文献\n\n"
        "[1] 某作者. 某书名. 某出版社, 2020.\n[2] 另一作者. 另一书名. 另一出版社, 2021.\n"
    )

    titles = {p["payload"]["title"] for p in _units(build_candidates_from_document("doc-bib", "b.pdf", markdown))}

    assert "参考文献" not in titles
    assert "第 6 章 常微分方程" in titles
    assert "6.1 欧拉方法" in titles


def test_propositions_are_recognised_as_anchors():
    """命题 is a claim with a proof; treating it as a plain heading lost the type
    and also reset the anchor, so the proof after it linked to nothing."""
    markdown = (
        "## 3.1 插值误差\n\n"
        "本节讨论插值多项式的误差表达，这些内容是后续数值积分构造的共同基础。\n\n"
        "命题 3.1 设 f 在节点上连续，则插值多项式存在且唯一，且误差有界。\n\n"
        "证明 由范德蒙行列式非零可知插值方程组有唯一解，余项由罗尔定理得到。\n"
    )

    sections = segment_document(markdown)
    proposition = next(s for s in sections if s.title.startswith("命题 3.1"))
    proof = next(s for s in sections if s.unit_type == "proof")

    assert proposition.unit_type == "theorem"
    assert proof.anchor_order == proposition.order

    relations = _relations(build_candidates_from_document("doc-prop", "b.pdf", markdown))
    assert any(r["payload"]["relation_type"] == "supports_proof" for r in relations)


def test_ocr_decorated_chapter_headings_are_not_front_matter():
    """MinerU emitted exercise headings as "K第 1 章 练习 k"; they are real content."""
    markdown = (
        "## 第 1 章 基础知识\n\n"
        "本章介绍误差来源与浮点数系统，这些内容是后续所有算法分析的共同基础。\n\n"
        "## K第 1 章 练习 k\n\n"
        "1. 用二分法求根，要求误差不超过 1e-6，问至少需要迭代多少次才够。\n"
    )

    titles = {p["payload"]["title"] for p in _units(build_candidates_from_document("doc-ocr", "b.pdf", markdown))}

    assert any("练习" in t for t in titles), titles


def test_marker_titles_drop_prose_but_keep_short_names():
    markdown = (
        "## 1.2 数值计算的误差\n\n"
        "本节讨论误差的来源与分类，这些内容是后续算法分析的共同基础，篇幅足够通过过滤。\n\n"
        "例题 1.1 (1) 多项式计算通常较为简单，我们可以设计一个算法来计算它的值。\n\n"
        "算法 2.1 二分法\n\n"
        "步骤一：取区间中点；步骤二：判断中点处函数符号；步骤三：保留异号半区间并重复。\n"
    )

    titles = {
        p["payload"]["title"]
        for p in _units(build_candidates_from_document("doc-title", "b.pdf", markdown))
    }

    assert "例题 1.1" in titles, titles
    assert not any("多项式计算通常较为简单" in t for t in titles)
    assert "算法 2.1 二分法" in titles, titles


def test_relations_do_not_cross_a_section_boundary():
    """A proof must not attach to a theorem from the previous section."""
    markdown = (
        "## 3.1 第一节\n\n"
        "定理 3.1 介值定理：若 f 连续且端点异号，则区间内至少存在一个零点成立。\n\n"
        "## 3.2 第二节\n\n"
        "本节的引言文字，长度足够通过最小长度过滤，用于承载这一节的说明内容。\n\n"
        "证明 该证明没有前置定理，因此不应该与上一节的定理建立任何关系边。\n"
    )

    proposals = build_candidates_from_document("doc-cross", "book.pdf", markdown)
    supports = [
        p for p in _relations(proposals) if p["payload"]["relation_type"] == "supports_proof"
    ]

    assert not supports, "a proof with no anchor in its own section must stay unlinked"


def test_long_theorem_proof_is_stored_in_full():
    """Content must not be capped at write time.

    On a real 150-page textbook a 600-char cap truncated 77% of units, threw
    away 75% of the body text, and cut 44 of 46 theorem proofs mid-LaTeX —
    including the conclusion, which is the entire point of the theorem.
    """
    filler = "由泰勒展开逐步推导热误差递推关系，" * 40
    markdown = (
        "## 定理 2.4 Newton 法的局部二次收敛性\n\n"
        f"令 x* 为 f(x) 的单根。证明 {filler}"
        "于是 $|e_{k+1}| \\leq \\frac{L}{d} |e_k|^2$，二次收敛性得证。\n"
    )

    proposals = build_candidates_from_document("doc-long", "book.pdf", markdown)

    assert len(proposals) == 1
    content = proposals[0]["payload"]["content"]
    assert len(content) > 600, "content must not be capped at write time"
    assert "二次收敛性得证" in content, "the conclusion must survive"
    assert content.count("{") == content.count("}")
    assert content.count("$") % 2 == 0


def test_candidates_from_document_requires_existing_document(client):
    res = client.post(
        "/api/courses/numerical_analysis/candidates/from-document",
        json={"document_id": "doc_missing"},
    )
    assert res.status_code == 404
