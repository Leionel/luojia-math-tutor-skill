import asyncio
import io
import os
import time
import zipfile

import httpx

# MinerU official API (v4), see https://mineru.net/apiManage/docs
# NOTE: the API token is issued with a ~90-day validity window on
# mineru.net — when uploads start failing with 401, regenerate the token
# and update MINERU_API_KEY in apps/api/.env.
FILE_URLS_API = "https://mineru.net/api/v4/file-urls/bear"
BATCH_RESULTS_API = "https://mineru.net/api/v4/extract-results/batch/"

POLL_INTERVAL_SECONDS = 2.0
POLL_TIMEOUT_SECONDS = 180.0


def _api_token() -> str:
    token = os.getenv("MINERU_API_KEY", "")
    if not token:
        raise RuntimeError(
            "MINERU_API_KEY is not configured. Create a token at "
            "https://mineru.net/apiManage (valid for ~90 days) and set it in apps/api/.env."
        )
    return token


def _markdown_from_zip(zip_bytes: bytes) -> str:
    """Extract the markdown document from a MinerU result zip."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".md")]
        if not names:
            raise RuntimeError("MinerU result zip contains no markdown file")
        # full.md is the canonical combined document; fall back to any .md
        preferred = next((n for n in names if n.lower().endswith("full.md")), names[0])
        return archive.read(preferred).decode("utf-8", errors="replace")


async def extract_markdown(filepath: str) -> str:
    """Upload a local document to MinerU and return its extracted markdown.

    Flow per https://mineru.net/apiManage/docs: request a presigned upload
    URL batch, PUT the file, then poll the batch until the result zip is
    ready.
    """
    filename = os.path.basename(filepath)
    token = _api_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Request a batch of presigned upload URLs
        res = await client.post(
            FILE_URLS_API,
            headers=headers,
            json={
                "enable_formula": True,
                "enable_table": True,
                "language": "ch",
                "files": [{"name": filename, "is_ocr": False}],
            },
        )
        res_data = res.json()
        if res_data.get("code") != 0:
            raise RuntimeError(f"Failed to create MinerU batch: {res_data.get('msg')}")
        batch_id = res_data["data"]["batch_id"]
        upload_url = res_data["data"]["file_urls"][0]

        # 2. Upload the file to the presigned OSS URL
        with open(filepath, "rb") as f:
            file_data = f.read()
        put_res = await client.put(upload_url, content=file_data, timeout=120.0)
        if put_res.status_code not in (200, 201):
            raise RuntimeError(f"Failed to upload file to MinerU OSS: {put_res.status_code}")

    # 3. Poll the batch result
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    async with httpx.AsyncClient(timeout=60.0) as client:
        while time.monotonic() < deadline:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            task_res = await client.get(
                f"{BATCH_RESULTS_API}{batch_id}", headers=headers
            )
            task_data = task_res.json()
            if task_data.get("code") != 0:
                raise RuntimeError(f"MinerU batch query failed: {task_data.get('msg')}")

            results = (task_data.get("data") or {}).get("extract_result") or []
            if not results:
                continue
            entry = results[0]
            state = entry.get("state")
            if state == "done":
                zip_url = entry.get("full_zip_url")
                if not zip_url:
                    raise RuntimeError("MinerU finished without a result zip URL")
                zip_res = await client.get(zip_url, timeout=120.0)
                zip_res.raise_for_status()
                return _markdown_from_zip(zip_res.content)
            if state == "failed":
                raise RuntimeError(f"MinerU parsing failed: {entry.get('err_msg', 'unknown error')}")
            # waiting-file | pending | running → keep polling

        raise RuntimeError("MinerU task polling timeout")


# Backwards-compatible alias for the previous entry point name.
extract_markdown_agent_api = extract_markdown
