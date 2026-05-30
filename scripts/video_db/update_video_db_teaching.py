import httpx
import asyncio
import json
import time
import os

# Combine all the keywords we used
ALL_KEYWORDS = [
    # 小学 K1-K6
    "四则运算", "加减法", "乘除法", "分数与小数", "百分数", "比例与反比例", "圆的周长与面积", 
    "鸡兔同笼", "抽屉原理", "植树问题", "行程问题", "相遇问题", "牛吃草问题", "奥数",
    
    # 初中 K7-K9
    "有理数", "无理数", "绝对值", "一次函数", "二次函数", "反比例函数", "一元一次方程", 
    "二元一次方程组", "一元二次方程", "勾股定理", "全等三角形", "相似三角形", 
    "平行四边形", "菱形与矩形", "圆的性质", "垂径定理", "切线长定理", "概率初步",
    
    # 高中 K10-K12
    "集合与逻辑用语", "幂函数", "指数函数", "对数函数", "三角函数", "正弦定理", "余弦定理",
    "数列", "等差数列", "等比数列", "平面向量", "空间向量", "立体几何", "三视图", 
    "解析几何", "直线与圆的方程", "圆锥曲线", "椭圆", "双曲线", "抛物线", 
    "高中导数", "函数极值与最值", "排列组合", "二项式定理", "复数代数形式", "极坐标系", "参数方程",
    
    # 本科及以上扩展
    "常微分方程", "偏微分方程", "实变函数", "泛函分析", "拓扑学", "抽象代数", "运筹学", "最优化理论",
    "线性规划", "非线性规划", "数值分析", "偏微分方程数值解", "随机过程",
    
    # 之前的一期关键字
    "高等数学", "微积分", "导数", "定积分", "不定积分", "偏导数", "多重积分", "级数", "泰勒展开", "微分方程",
    "洛必达法则", "拉格朗日中值定理", "柯西中值定理", "斯托克斯公式", "格林公式", "高斯公式",
    "线性代数", "矩阵乘法", "行列式", "逆矩阵", "特征值与特征向量", "对角化", "二次型", "正交变换", "奇异值分解 SVD",
    "概率论", "随机变量", "期望与方差", "大数定律", "中心极限定理", "正态分布", "泊松分布", "二项分布", "贝叶斯定理", "马尔可夫链",
    "假设检验", "最大似然估计", "置信区间", "协方差",
    "深度学习", "神经网络", "反向传播", "梯度下降", "Transformer", "CNN", "RNN", "LSTM", "注意力机制", "强化学习",
    "时间序列", "傅里叶变换", "拉普拉斯变换", "复变函数", "离散数学", "图论", "数学建模"
]

# De-duplicate
ALL_KEYWORDS = list(set(ALL_KEYWORDS))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": "buvid3=D44F2E1E-B9AB-7B93-DE44-24E48DF42E4349141infoc;"
}

async def fetch_keyword(client, original_kw):
    # 为保证搜索质量，拼接细化关键词
    search_kw = f"{original_kw} 教学 讲解"
    
    url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={search_kw}"
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
                print(f"[OK] {original_kw} (Searched: {search_kw}) -> {len(results)} videos")
                return original_kw, results
    except Exception as e:
        print(f"[FAIL] {original_kw} failed: {e}")
    return original_kw, []

async def main():
    db_path = "apps/api/data/fallback_videos.json"
    
    # We will completely overwrite or merge. Let's merge but OVERWRITE existing keys 
    # to ensure they have the new high-quality teaching videos.
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {}
        
    print(f"Loaded existing DB with {len(db)} keywords. Starting refinement overwrite...")
    
    updated_count = 0
    async with httpx.AsyncClient() as client:
        for kw in ALL_KEYWORDS:
            kw, res = await fetch_keyword(client, kw)
            if res:
                db[kw] = res
                updated_count += 1
            time.sleep(0.5) # delay to avoid rate limit
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\nDone! Updated {updated_count} keywords with high-quality teaching queries. Total keywords: {len(db)}")

if __name__ == "__main__":
    asyncio.run(main())
