from fastapi import APIRouter
import httpx

router = APIRouter(prefix="/api", tags=["Resources"])

@router.get("/resources/bilibili/search")
async def search_bilibili(keyword: str):
    url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={keyword}"
    
    # We use a mocked hardcoded list for demonstration if Bilibili blocks us
    # but let's try the real API first with a spoofed user-agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": "buvid3=D44F2E1E-B9AB-7B93-DE44-24E48DF42E4349141infoc;"
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            data = resp.json()
            
            if data.get("code") == 0:
                results = []
                for item in data.get("data", {}).get("result", []):
                    if item.get("result_type") == "video":
                        videos = item.get("data", [])
                        for v in videos[:3]:
                            results.append({
                                "bvid": v.get("bvid"),
                                "title": v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                                "pic": "http:" + v.get("pic", "") if v.get("pic", "").startswith("//") else v.get("pic", ""),
                                "author": v.get("author")
                            })
                        break
                if results:
                    return results
    except Exception as e:
        print(f"Bilibili search failed: {e}")
        
    # Fallback mock data
    kw_lower = keyword.lower()
    
    # Try to load the big fallback DB
    fallback_db_path = Path("app/data/fallback_videos.json")
    if not fallback_db_path.exists():
        fallback_db_path = Path("data/fallback_videos.json")
    
    if fallback_db_path.exists():
        try:
            with open(fallback_db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            # Direct match
            for k in db:
                if k.lower() == kw_lower:
                    if db[k]: return db[k]
                    
            # Substring match (e.g. user asks "讲一下Transformer" -> matches "Transformer")
            for k in db:
                if k.lower() in kw_lower or kw_lower in k.lower():
                    if db[k]: return db[k]
        except Exception as fallback_e:
            print(f"Error loading fallback db: {fallback_e}")

    # Ultimate fallback if everything fails
    if "transformer" in kw_lower:
        return [
            {
                "bvid": "BV1fj6vBfEnu",
                "title": "【Transformer】最强动画讲解！从理论到实战，通俗易懂解释原理",
                "pic": "http://i2.hdslb.com/bfs/archive/ab93cffa150accdb552487147bfe563d99e9130a.jpg",
                "author": "哔哩人工智能学院"
            }
        ]
    return []
