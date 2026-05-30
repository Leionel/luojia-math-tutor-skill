import httpx
import asyncio
import json
import time
import os

NEW_KEYWORDS = [
    # 小学 K1-K6
    "四则运算", "加减法", "乘除法", "分数与小数", "百分数", "比例与反比例", "圆的周长与面积", 
    "鸡兔同笼", "抽屉原理", "植树问题", "行程问题", "相遇问题", "牛吃草问题", "奥数",
    
    # 初中 K7-K9
    "有理数与无理数", "绝对值", "一次函数", "二次函数", "反比例函数", "一元一次方程", 
    "二元一次方程组", "一元二次方程", "勾股定理", "全等三角形", "相似三角形", 
    "平行四边形", "菱形与矩形", "圆的性质", "垂径定理", "切线长定理", "概率初步",
    
    # 高中 K10-K12
    "集合与逻辑用语", "幂函数", "指数函数", "对数函数", "三角函数", "正弦定理", "余弦定理",
    "数列", "等差数列", "等比数列", "平面向量", "空间向量", "立体几何", "三视图", 
    "解析几何", "直线与圆的方程", "圆锥曲线", "椭圆", "双曲线", "抛物线", 
    "高中导数", "函数极值与最值", "排列组合", "二项式定理", "复数代数形式", "极坐标系", "参数方程",
    
    # 本科及以上扩展
    "常微分方程", "偏微分方程", "实变函数", "泛函分析", "拓扑学", "抽象代数", "运筹学", "最优化理论",
    "线性规划", "非线性规划", "数值分析", "偏微分方程数值解", "随机过程"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": "buvid3=D44F2E1E-B9AB-7B93-DE44-24E48DF42E4349141infoc;"
}

async def fetch_keyword(client, kw):
    url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={kw}"
    try:
        resp = await client.get(url, headers=HEADERS, timeout=5.0)
        data = resp.json()
        if data.get("code") == 0:
            results = []
            for item in data.get("data", {}).get("result", []):
                if item.get("result_type") == "video":
                    videos = item.get("data", [])
                    for v in videos[:5]: # top 5
                        results.append({
                            "bvid": v.get("bvid"),
                            "title": v.get("title", "").replace('<em class="keyword">', '').replace('</em>', ''),
                            "pic": "http:" + v.get("pic", "") if v.get("pic", "").startswith("//") else v.get("pic", ""),
                            "author": v.get("author")
                        })
                    break
            if results:
                print(f"[OK] {kw} ({len(results)} videos)")
                return kw, results
    except Exception as e:
        print(f"[FAIL] {kw} failed: {e}")
    return kw, []

async def main():
    db_path = "apps/api/data/fallback_videos.json"
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {}
        
    print(f"Loaded existing DB with {len(db)} keywords.")
    
    added_count = 0
    async with httpx.AsyncClient() as client:
        for kw in NEW_KEYWORDS:
            if kw in db and len(db[kw]) > 0:
                continue
            
            kw, res = await fetch_keyword(client, kw)
            if res:
                db[kw] = res
                added_count += 1
            time.sleep(1) # delay to avoid rate limit
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\nDone! Added {added_count} new keywords. Total keywords: {len(db)}")

if __name__ == "__main__":
    asyncio.run(main())
