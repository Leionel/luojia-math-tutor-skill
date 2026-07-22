import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json

from app.main import app
from app.config import get_settings, Settings

client = TestClient(app)

@pytest.fixture
def mock_output_dir(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    mock_data = {
        "units": [
            {
                "id": "u1",
                "content": "test content",
                "title": "test title",
                "latex": "test latex",
                "review_status": "draft"
            },
            {
                "id": "u2",
                "content": "another",
                "review_status": "active"
            }
        ],
        "relations": [
            {
                "source_unit_id": "u1",
                "target_unit_id": "u2",
                "relation_type": "prereq",
                "review_status": "draft"
            }
        ]
    }
    
    with open(output_dir / "m1_test.json", "w", encoding="utf-8") as f:
        json.dump(mock_data, f)
        
    class MockSettings(Settings):
        @property
        def knowledge_root(self) -> Path:
            return tmp_path
            
    app.dependency_overrides[get_settings] = MockSettings
    yield output_dir
    app.dependency_overrides.clear()

def test_get_pending_knowledge(mock_output_dir):
    res = client.get("/api/admin/knowledge/pending")
    assert res.status_code == 200
    data = res.json()
    assert len(data["units"]) == 1
    assert data["units"][0]["id"] == "u1"
    assert len(data["relations"]) == 1
    assert data["relations"][0]["review_status"] == "draft"

def test_update_unit(mock_output_dir):
    res = client.put("/api/admin/knowledge/units/u1", json={"title": "new title", "content": "new content"})
    assert res.status_code == 200
    
    # check file
    with open(mock_output_dir / "m1_test.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["units"][0]["title"] == "new title"
    assert data["units"][0]["content"] == "new content"
    assert data["units"][0]["latex"] == "test latex" # unmodified

def test_review_knowledge_approve(mock_output_dir):
    rel_id = "u1_u2_prereq"
    res = client.post("/api/admin/knowledge/review", json={"unit_ids": ["u1"], "relation_ids": [rel_id], "action": "approve"})
    assert res.status_code == 200
    
    # check file
    with open(mock_output_dir / "m1_test.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["units"][0]["review_status"] == "active"
    assert data["relations"][0]["review_status"] == "active"

def test_review_knowledge_reject(mock_output_dir):
    rel_id = "u1_u2_prereq"
    res = client.post("/api/admin/knowledge/review", json={"unit_ids": ["u1"], "relation_ids": [rel_id], "action": "reject"})
    assert res.status_code == 200
    
    # check file
    with open(mock_output_dir / "m1_test.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["units"][0]["review_status"] == "rejected"
    assert data["relations"][0]["review_status"] == "rejected"

def test_publish_knowledge(mock_output_dir):
    # Setup mock data with mix of active and draft
    with open(mock_output_dir / "m1_test.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data["relations"].append({
        "source_unit_id": "u2",
        "target_unit_id": "u3",
        "relation_type": "prereq",
        "review_status": "active"
    })
    data["units"].append({
        "id": "u3",
        "content": "u3 content",
        "review_status": "active"
    })
    with open(mock_output_dir / "m1_test.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    res = client.post("/api/admin/knowledge/publish")
    assert res.status_code == 200
    
    # Check published_knowledge.json is created
    pub_path = mock_output_dir / "published_knowledge.json"
    assert pub_path.exists()
    
    with open(pub_path, "r", encoding="utf-8") as f:
        pub_data = json.load(f)
        
    assert len(pub_data["units"]) == 2
    ids = [u["id"] for u in pub_data["units"]]
    assert "u2" in ids
    assert "u3" in ids
    assert len(pub_data["relations"]) == 1
    assert pub_data["relations"][0]["source_unit_id"] == "u2"
    
    # Check graph map
    graph_path = mock_output_dir / "prerequisites_graph.json"
    assert graph_path.exists()
    with open(graph_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)
    assert "u3" in graph_data
    assert graph_data["u3"] == ["u2"]

