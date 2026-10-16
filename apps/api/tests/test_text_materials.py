"""User text becomes an immutable existing document, never a model or gold reply."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.auth import Principal, get_principal
from app.config import Settings
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.memory.repository import Repository
from app.tutor.learning_workspace import LearningWorkspace
from app.tutor.learning_context import ReadingContextRef, resolve_learning_context
from app.api import routes_learning


@pytest.fixture
def material_client(tmp_path, monkeypatch):
    service = LearningWorkspace(CourseService(store=CourseStore(str(tmp_path / "course.db"))),
        Repository(Settings(database_url=f"sqlite:///{tmp_path / 'student.db'}")))
    monkeypatch.setattr(routes_learning, "workspace", lambda: service)
    app = FastAPI(); app.include_router(routes_learning.router)
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    with TestClient(app) as client:
        yield client, app, service
    service.store.close()


def test_text_material_keeps_original_unicode_and_prior_source(material_client):
    client, app, service = material_client
    text = "# 我的讲义\n\nδ 不能依赖 x。🧮\n\n<script>资料，不执行</script>"
    first = client.post("/api/reading/documents", json={"title":"讲义.md", "text":text})
    assert first.status_code == 201
    old = first.json()
    assert service.repository.get_document_markdown(old["id"], "alice") == text
    second = client.post("/api/reading/documents", json={"title":"讲义.md", "text":"修订的原文"}).json()
    assert second["id"] != old["id"] and second["source_hash"] != old["source_hash"]
    assert client.get(f"/api/reading/documents/{old['id']}").json() == old
    section = old["sections"][0]
    ref = ReadingContextRef(kind="reading", source_id=old["id"], source_hash=old["source_hash"],
        section_id=section["id"], start=0, end=len(section["quote"]), graph_revision=None)
    result = resolve_learning_context(service, "alice", ref)
    assert result["citation"]["quote"] == section["quote"]
    assert result["independent_success"] is False
    with pytest.raises((KeyError, ValueError)):
        resolve_learning_context(service, "bob", ref)
    with pytest.raises(ValueError):
        resolve_learning_context(service, "alice", ref.model_copy(update={"source_hash":second["source_hash"]}))
    app.dependency_overrides[get_principal] = lambda: Principal("bob", True)
    assert client.get(f"/api/reading/documents/{old['id']}").status_code == 404
    assert client.get("/api/reading/documents").json()["documents"] == []


@pytest.mark.parametrize("payload", [{"title":"", "text":"x"}, {"title":"  ", "text":"x"},
    {"title":"a", "text":" "}, {"title":"a", "text":"x"*20001}, {"title":"a", "text":"x\x00y"},
    {"title":"a", "text":"x", "owner":"bob"}])
def test_text_material_rejects_invalid_or_spoofed_input(material_client, payload):
    client, _, service = material_client
    assert client.post("/api/reading/documents", json=payload).status_code == 422
    assert service.repository.list_documents("alice") == []


def test_text_material_requires_login_and_context_keeps_help_boundary(material_client):
    client, app, service = material_client
    app.dependency_overrides[get_principal] = lambda: Principal("demo-user", False)
    assert client.post("/api/reading/documents", json={"title":"a", "text":"source"}).status_code == 401
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    saved = client.post("/api/reading/documents", json={"title":"a", "text":"原文"}).json()
    service.new_assessment("alice")
    ref = ReadingContextRef(kind="reading", source_id=saved["id"], source_hash=saved["source_hash"],
        section_id=saved["sections"][0]["id"], start=0, end=2, graph_revision=None)
    with pytest.raises(ValueError):
        resolve_learning_context(service, "alice", ref)
