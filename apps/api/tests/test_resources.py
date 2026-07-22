from unittest.mock import AsyncMock

import httpx
from fastapi.testclient import TestClient

from app.main import app


def test_bilibili_search_uses_fallback_when_network_fails(monkeypatch):
    async def fail_get(*args, **kwargs):
        raise httpx.HTTPError("network unavailable")

    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(side_effect=fail_get))

    client = TestClient(app)
    response = client.get("/api/resources/bilibili/search", params={"keyword": "transformer"})

    assert response.status_code == 200
    videos = response.json()
    assert videos
    assert videos[0]["bvid"]
