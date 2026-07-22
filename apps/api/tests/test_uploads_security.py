from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes_uploads
from app.main import app


def test_rejects_path_traversal_download(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("hidden", encoding="utf-8")
    monkeypatch.setattr(routes_uploads, "UPLOAD_DIR", upload_dir)

    client = TestClient(app)
    response = client.get("/api/uploads/..%5Csecret.txt")

    assert response.status_code == 404
    assert response.text != "hidden"


def test_rejects_unsupported_upload_extension(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(routes_uploads, "UPLOAD_DIR", upload_dir)

    client = TestClient(app)
    response = client.post(
        "/api/uploads",
        files={"file": ("payload.exe", b"not really an image", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert list(Path(upload_dir).iterdir()) == []
