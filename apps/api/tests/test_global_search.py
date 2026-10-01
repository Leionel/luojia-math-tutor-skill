import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.knowledge.schema import KnowledgeItem


@pytest.fixture
def client():
    return TestClient(app)


def test_global_search_curriculum_success(client, monkeypatch):
    mock_items = (
        KnowledgeItem(
            id="taylor_theorem",
            subject="calculus",
            source_file="concept_gs.json",
            concept_zh="泰勒中值定理",
            prerequisite=[],
            description="如果函数f(x)在闭区间[a,b]上具有直到n阶的连续导数...",
            intuitive_explanation="",
            solution="f(x) = f(x_0) + f'(x_0)(x - x_0) + ...",
            chapter="第三章 中值定理",
            section="第二节 泰勒公式",
            type="theorem",
        ),
        KnowledgeItem(
            id="matrix_rank",
            subject="linear_algebra",
            source_file="la.json",
            concept_zh="矩阵的秩",
            prerequisite=[],
            description="矩阵中非零子式的最高阶数称为矩阵的秩。",
            intuitive_explanation="",
            solution="",
            chapter="第二章 矩阵",
            section="第三节 矩阵的秩",
            type="definition",
        ),
    )

    monkeypatch.setattr("app.api.routes_search.load_knowledge", lambda: mock_items)

    # 1. 搜索泰勒
    resp = client.get("/api/search/global?q=泰勒&category=curriculum")
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "泰勒"
    assert data["category"] == "curriculum"
    assert data["total"] == 1
    assert data["items"][0]["title"] == "泰勒中值定理"
    assert data["items"][0]["formula"] == "f(x) = f(x_0) + f'(x_0)(x - x_0) + ..."

    # 2. 搜索矩阵
    resp2 = client.get("/api/search/global?q=矩阵&category=curriculum")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total"] == 1
    assert data2["items"][0]["title"] == "矩阵的秩"

    # 3. 搜索不相关的词
    resp3 = client.get("/api/search/global?q=未命中的词语xyz&category=curriculum")
    assert resp3.status_code == 200
    assert resp3.json()["total"] == 0
