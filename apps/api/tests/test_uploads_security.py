from pathlib import Path

from fastapi.testclient import TestClient
from fastapi import FastAPI
import pytest

from app.api import routes_auth, routes_uploads
from app.agents.multimodal import normalize_image_reference
from app.auth import Principal, get_principal
from app.config import Settings
from app.main_deps import get_app_settings, get_repository
from app.main import app
from app.memory.repository import Repository


def test_rejects_path_traversal_download(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("hidden", encoding="utf-8")
    monkeypatch.setattr(routes_uploads, "UPLOAD_DIR", upload_dir)

    client = TestClient(app)
    response = client.get("/api/uploads/..%5Csecret.txt")
    assert response.status_code == 401
    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    response = client.get("/api/uploads/..%5Csecret.txt")
    assert response.status_code == 404
    assert response.text != "hidden"
    app.dependency_overrides.clear()


def test_rejects_unsupported_upload_extension(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(routes_uploads, "UPLOAD_DIR", upload_dir)

    app.dependency_overrides[get_principal] = lambda: Principal("alice", True)
    client = TestClient(app)
    response = client.post(
        "/api/uploads",
        files={"file": ("payload.exe", b"not really an image", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert list(Path(upload_dir).iterdir()) == []
    app.dependency_overrides.clear()


@pytest.fixture
def upload_app(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(routes_uploads, "UPLOAD_DIR", upload_dir)
    async def no_extraction(_path):
        return ""
    monkeypatch.setattr(routes_uploads, "extract_markdown_agent_api", no_extraction)
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'uploads.db'}", auth_required=True,
                        auth_token_secret="offline-test-secret-01234567890123456789")
    repository = Repository(settings)
    isolated = FastAPI()
    isolated.include_router(routes_auth.router)
    isolated.include_router(routes_uploads.router)
    isolated.dependency_overrides[get_app_settings] = lambda: settings
    isolated.dependency_overrides[get_repository] = lambda: repository
    client = TestClient(isolated)
    def token(user):
        response = client.post("/api/auth/register", json={"user_id": user, "password": "synthetic-passphrase-123"})
        assert response.status_code == 201
        return response.json()["access_token"]
    return client, repository, upload_dir, token


def test_uploaded_file_requires_live_owner_session(upload_app):
    client, repository, upload_dir, token = upload_app
    alice = token("alice")
    bob = token("bob")
    owner = {"Authorization": f"Bearer {alice}"}
    other = {"Authorization": f"Bearer {bob}"}
    assert client.post("/api/uploads", files={"file": ("anonymous.png", b"x", "image/png")}).status_code == 401
    assert list(upload_dir.iterdir()) == []
    response = client.post("/api/uploads", headers=owner,
                           files={"file": ("figure.png", b"image bytes", "image/png")})
    assert response.status_code == 200
    url = response.json()["url"]
    filename = url.rsplit("/", 1)[-1]
    assert (upload_dir / filename).is_file()
    assert client.get(url, headers=owner).content == b"image bytes"
    assert client.get(url, headers=owner).headers["cache-control"] == "private, no-store"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=other).status_code == 404
    assert client.get("/api/uploads/" + "0" * 8 + "-0000-0000-0000-000000000000.png", headers=owner).status_code == 404
    unowned = "11111111-1111-1111-1111-111111111111.png"
    (upload_dir / unowned).write_bytes(b"old file")
    assert client.get("/api/uploads/" + unowned, headers=owner).status_code == 404
    assert client.post("/api/auth/logout", headers=owner).status_code == 200
    assert client.get(url, headers=owner).status_code == 401
    assert not repository.uploaded_file_belongs_to(filename, "bob")


def test_image_normalization_checks_owner_before_read(upload_app):
    client, repository, upload_dir, token = upload_app
    alice = token("alice")
    response = client.post("/api/uploads", headers={"Authorization": f"Bearer {alice}"},
                           files={"file": ("figure.png", b"image bytes", "image/png")})
    reference = response.json()["url"]
    assert normalize_image_reference(reference, upload_dir, "alice", repository).startswith("data:image/png;base64,")
    with pytest.raises(ValueError, match="not found"):
        normalize_image_reference(reference, upload_dir, "bob", repository)
    with pytest.raises(ValueError, match="not found"):
        normalize_image_reference("/api/uploads/11111111-1111-1111-1111-111111111111.png", upload_dir, "alice", repository)
