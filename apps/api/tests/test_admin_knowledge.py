"""Legacy files are readable by teachers, but can no longer publish official facts."""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api import routes_admin_knowledge
from app.auth import Principal, get_principal


@pytest.fixture
def legacy(tmp_path, monkeypatch):
    output = tmp_path / "output"
    output.mkdir()
    source = output / "m1_test.json"
    source.write_text(
        json.dumps(
            {
                "units": [
                    {
                        "id": "u1",
                        "title": "test",
                        "content": "original",
                        "review_status": "draft",
                    }
                ],
                "relations": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(routes_admin_knowledge, "get_output_dir", lambda _: output)
    app = FastAPI()
    app.include_router(routes_admin_knowledge.router)
    app.dependency_overrides[get_principal] = lambda: Principal(
        "teacher", True, "teacher"
    )
    with TestClient(app) as client:
        yield client, source


def test_get_knowledge_list(legacy):
    client, source = legacy
    response = client.get("/api/admin/knowledge/list")
    assert response.status_code == 200
    assert response.json()["units"][0]["content"] == "original"


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("put", "/api/admin/knowledge/units/u1", {"content": "override"}),
        (
            "post",
            "/api/admin/knowledge/review",
            {"unit_ids": ["u1"], "action": "approve"},
        ),
        (
            "post",
            "/api/admin/knowledge/review",
            {"unit_ids": ["u1"], "action": "reject"},
        ),
        ("post", "/api/admin/knowledge/publish", {}),
    ],
)
def test_legacy_mutations_are_retired_without_file_changes(legacy, method, path, body):
    client, source = legacy
    before = source.read_bytes()
    response = getattr(client, method)(path, json=body)
    assert response.status_code == 410
    assert source.read_bytes() == before
    assert sorted(p.name for p in source.parent.iterdir()) == ["m1_test.json"]
