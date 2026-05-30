import httpx
import asyncio
import json
import time
import os

KEYWORDS = [
    "高等数学", "微积分", "导数", "定积分", "不定积分", "偏导数", "多重积分", "级数", "泰勒展开", "微分方程",
    "洛必达法则", "拉格朗日中值定理", "柯西中值定理", "斯托克斯公式", "格林公式", "高斯公式",
    "线性代数", "矩阵乘法", "行列式", "逆矩阵", "特征值与特征向量", "对角化", "二次型", "正交变换", "奇异值分解 SVD",
    "概率论", "随机变量", "期望与方差", "大数定律", "中心极限定理", "正态分布", "泊松分布", "二项分布", "贝叶斯定理", "马尔可夫链",
    "假设检验", "最大似然估计", "置信区间", "协方差",
    "深度学习", "神经网络", "反向传播", "梯度下降", "Transformer", "CNN", "RNN", "LSTM", "注意力机制", "强化学习",
    "时间序列", "傅里叶变换", "拉普拉斯变换", "复变函数", "离散数学", "图论", "数学建模"
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
    db = {}
    async with httpx.AsyncClient() as client:
        for kw in KEYWORDS:
            kw, res = await fetch_keyword(client, kw)
            if res:
                db[kw] = res
            time.sleep(1) # delay to avoid rate limit
    
    out_dir = "apps/api/data"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "fallback_videos.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\nDone! Saved {len(db)} keywords to {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
