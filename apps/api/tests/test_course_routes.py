import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.knowledge.course_service import get_course_service


@pytest.fixture
def client():
    return TestClient(app)


def test_get_course_graph_react_flow(client):
    response = client.get("/api/courses/numerical_analysis/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["total_nodes"] >= 20
    assert data["total_edges"] >= 15

    # Check a specific node structure
    newton_node = next((n for n in data["nodes"] if n["id"] == "NA_NEWTON"), None)
    assert newton_node is not None
    assert newton_node["data"]["label"] == "牛顿迭代法 (Newton-Raphson Method)"
    assert newton_node["data"]["scope"] == "core"


def test_get_course_graph_raw_format(client):
    response = client.get("/api/courses/numerical_analysis/graph?format=raw")
    assert response.status_code == 200
    data = response.json()
    assert data["course_id"] == "numerical_analysis"
    assert len(data["units"]) >= 20
    assert len(data["relations"]) >= 15


def test_get_course_subgraph(client):
    response = client.get("/api/courses/numerical_analysis/graph/subgraph?unit_id=NA_NEWTON&depth=1")
    assert response.status_code == 200
    data = response.json()
    assert data["center_unit_id"] == "NA_NEWTON"
    assert len(data["units"]) >= 2
    assert len(data["relations"]) >= 1


def test_list_and_match_cases(client):
    # 1. List cases
    res_list = client.get("/api/courses/numerical_analysis/cases")
    assert res_list.status_code == 200
    cases_data = res_list.json()
    assert cases_data["total"] >= 10

    # 2. Match exact query
    match_payload = {
      "query": "为什么牛顿法初值选不好会发散",
      "context": {"task_mode": "error_debugging"}
    }
    res_match = client.post("/api/courses/numerical_analysis/cases/match", json=match_payload)
    assert res_match.status_code == 200
    match_data = res_match.json()
    assert match_data["matched_case_id"] == "CASE_NEWTON_INITIAL_VALUE"
    assert match_data["decision"] in ("SAME_CASE", "VARIANT_OF_CASE")
    assert match_data["confidence"] >= 0.5


def test_candidate_lifecycle_routes(client):
    cand_id = "test_cand_broyden"
    # 1. Create candidate
    create_payload = {
        "candidate_id": cand_id,
        "candidate_type": "new_unit",
        "payload": {
            "id": "NA_BROYDEN",
            "title": "Broyden 拟牛顿法",
            "type": "algorithm",
            "content": "使用秩一修正近似雅可比矩阵。"
        },
        "proposed_by": "teacher",
        "evidence_ref": "exam_q5"
    }
    res_create = client.post("/api/courses/numerical_analysis/candidates", json=create_payload)
    assert res_create.status_code == 200
    assert res_create.json()["status"] == "created"

    # 2. List candidates
    res_list = client.get("/api/courses/numerical_analysis/candidates")
    assert res_list.status_code == 200
    assert any(c["candidate_id"] == cand_id for c in res_list.json()["candidates"])

    # 3. Review candidate (approve)
    review_payload = {
        "action": "approve",
        "reviewer_id": "prof_li",
        "review_note": "Approved for advanced numerical analysis extension."
    }
    res_review = client.post(f"/api/courses/numerical_analysis/candidates/{cand_id}/review", json=review_payload)
    assert res_review.status_code == 200
    assert res_review.json()["status"] == "success"


def test_student_overlay_routes(client):
    student_id = "student_test_001"
    course_id = "numerical_analysis"

    # 1. Record event
    event_payload = {
        "event_id": "evt_999",
        "unit_ids": ["NA_BISECTION"],
        "case_id": "CASE_BISECTION_REQUIREMENTS",
        "event_type": "attempt",
        "is_independent": True,
        "is_success": True,
        "help_level": 0
    }
    res_evt = client.post(f"/api/courses/users/{student_id}/{course_id}/events", json=event_payload)
    assert res_evt.status_code == 200

    # 2. Get student overlay
    res_overlay = client.get(f"/api/courses/users/{student_id}/{course_id}/overlay")
    assert res_overlay.status_code == 200
    overlay_data = res_overlay.json()
    assert "NA_BISECTION" in overlay_data["units"]
    assert overlay_data["units"]["NA_BISECTION"]["independent_evidence_count"] >= 1
    assert "CASE_BISECTION_REQUIREMENTS" in overlay_data["cases"]
    assert overlay_data["cases"]["CASE_BISECTION_REQUIREMENTS"]["latest_outcome"] == "success"
