import html
import json
import re
from pathlib import Path

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Resources"])

FALLBACK_VIDEO_DB = Path(__file__).resolve().parents[2] / "data" / "fallback_videos.json"


def _plain_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    return re.sub(r"<[^>]+>", "", text).strip()


def _normalize_video(raw: dict) -> dict:
    pic = str(raw.get("pic") or "")
    return {
        "bvid": _plain_text(raw.get("bvid")),
        "title": _plain_text(raw.get("title")),
        "pic": f"https:{pic}" if pic.startswith("//") else pic,
        "author": _plain_text(raw.get("author")),
    }


def _fallback_videos(keyword: str) -> list[dict]:
    kw_lower = keyword.lower()

    if FALLBACK_VIDEO_DB.exists():
        try:
            with open(FALLBACK_VIDEO_DB, "r", encoding="utf-8") as f:
                db = json.load(f)

            for key, videos in db.items():
                if key.lower() == kw_lower and videos:
                    return [_normalize_video(video) for video in videos[:3]]

            for key, videos in db.items():
                if videos and (key.lower() in kw_lower or kw_lower in key.lower()):
                    return [_normalize_video(video) for video in videos[:3]]
        except Exception as exc:
            print(f"Error loading fallback db: {exc}")

    if "transformer" in kw_lower:
        return [
            _normalize_video(
                {
                    "bvid": "BV1fj6vBfEnu",
                    "title": "Transformer introduction",
                    "pic": "https://i2.hdslb.com/bfs/archive/ab93cffa150accdb552487147bfe563d99e9130a.jpg",
                    "author": "AI course",
                }
            )
        ]
    return []


@router.get("/resources/bilibili/search")
async def search_bilibili(keyword: str):
    url = "https://api.bilibili.com/x/web-interface/search/all/v2"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params={"keyword": keyword}, headers=headers)
            data = resp.json()

            if data.get("code") == 0:
                for item in data.get("data", {}).get("result", []):
                    if item.get("result_type") != "video":
                        continue
                    videos = item.get("data", [])
                    results = [_normalize_video(video) for video in videos[:3]]
                    if results:
                        return results
                    break
    except Exception as exc:
        print(f"Bilibili search failed: {exc}")

    return _fallback_videos(keyword)
