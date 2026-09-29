"""Offline tests for the MinerU v4 client.

No network access: responses are constructed with `httpx.Response` directly.
"""

import io
import zipfile

import httpx
import pytest

from app.services.mineru_client import (
    BATCH_RESULTS_API,
    FILE_URLS_API,
    _markdown_from_zip,
    _parse_json,
)


def _response(status_code: int, body: bytes, content_type: str) -> httpx.Response:
    return httpx.Response(
        status_code,
        content=body,
        headers={"content-type": content_type},
        request=httpx.Request("POST", FILE_URLS_API),
    )


def test_batch_endpoint_paths_match_the_v4_api() -> None:
    """Regression: `file-urls/bear` 404'd and killed the whole upload path."""
    assert FILE_URLS_API.endswith("/api/v4/file-urls/batch")
    assert BATCH_RESULTS_API.endswith("/api/v4/extract-results/batch/")


def test_parse_json_returns_the_payload() -> None:
    res = _response(200, b'{"code":0,"msg":"ok","data":{"batch_id":"b1"}}', "application/json")

    data = _parse_json(res, "batch creation")

    assert data["code"] == 0
    assert data["data"]["batch_id"] == "b1"


def test_parse_json_reports_a_plain_text_404_clearly() -> None:
    """MinerU answers unknown paths with plain text, not JSON."""
    res = _response(404, b"404 page not found\n", "text/plain; charset=utf-8")

    with pytest.raises(RuntimeError) as excinfo:
        _parse_json(res, "batch creation")

    message = str(excinfo.value)
    assert "404" in message
    assert "page not found" in message
    assert "non-JSON" not in message or "404" in message
    # The underlying JSONDecodeError must not be what surfaces to the user.
    assert "Extra data" not in message


def test_parse_json_points_at_token_expiry_on_401() -> None:
    res = _response(401, b'{"code":401,"msg":"unauthorized"}', "application/json")

    with pytest.raises(RuntimeError) as excinfo:
        _parse_json(res, "batch creation")

    message = str(excinfo.value)
    assert "401" in message
    assert "90 days" in message
    assert "MINERU_API_KEY" in message


def test_parse_json_reports_server_errors_with_a_snippet() -> None:
    res = _response(503, b"upstream unavailable", "text/plain")

    with pytest.raises(RuntimeError) as excinfo:
        _parse_json(res, "batch status query")

    assert "503" in str(excinfo.value)
    assert "upstream unavailable" in str(excinfo.value)


def test_parse_json_rejects_a_non_object_payload() -> None:
    res = _response(200, b"[1,2,3]", "application/json")

    with pytest.raises(RuntimeError, match="unexpected JSON"):
        _parse_json(res, "batch creation")


def _zip_with(entries: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in entries.items():
            archive.writestr(name, text)
    return buffer.getvalue()


def test_markdown_from_zip_prefers_full_md() -> None:
    payload = _zip_with({"auto/layout.md": "# partial", "full.md": "# 第2章 完整文档"})

    assert _markdown_from_zip(payload).strip() == "# 第2章 完整文档"


def test_markdown_from_zip_falls_back_to_any_markdown() -> None:
    payload = _zip_with({"output/chapter.md": "# 单文件结果"})

    assert _markdown_from_zip(payload).strip() == "# 单文件结果"


def test_markdown_from_zip_without_markdown_is_an_explicit_failure() -> None:
    payload = _zip_with({"content.json": "{}"})

    with pytest.raises(RuntimeError, match="no markdown file"):
        _markdown_from_zip(payload)
