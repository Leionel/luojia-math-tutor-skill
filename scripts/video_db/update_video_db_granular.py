import httpx
import asyncio
import json
import time
import os

GRANULAR_KEYWORDS = [
    # 小学微观概念
    "凑十法", "破十法", "最小公倍数求法", "最大公约数", "分数乘除法计算技巧",
    "植树问题公式", "牛吃草问题解法", "同向追及问题", "相向相遇问题", "容斥原理应用",
    
    # 初中微观概念
    "十字相乘法", "配方法解一元二次方程", "一元二次方程求根公式", "韦达定理应用", 
    "二次方程判别式", "因式分解技巧", "二次函数顶点坐标公式", "二次函数最值问题", 
    "二次函数图像平移", "三角形中位线定理", "勾股定理逆定理", "射影定理", 
    "圆周角定理", "切线判定定理", "黄金分割比计算",
    
    # 高中微观概念
    "函数奇偶性判定", "函数单调性证明", "复合函数求导法则", "隐函数求导", 
    "对数换底公式", "三角函数诱导公式", "和差化积公式", "积化和差公式", 
    "二倍角公式", "辅助角公式提取", "裂项相消法", "错位相减法求和", 
    "数学归纳法证明", "均值不等式应用", "柯西不等式", "向量数量积计算", 
    "平面法向量求法", "空间直角坐标系建立", "二面角求法", "直线弦长公式", 
    "点到直线距离公式", "线性规划图解法", "二项式展开式常数项求法",
    
    # 大学微积分/高数微观概念
    "等价无穷小替换", "夹逼定理证明极限", "泰勒公式皮亚诺余项", "拉格朗日余项", 
    "变限积分求导", "牛顿莱布尼茨公式应用", "分部积分法", "第二类换元积分法", 
    "反常积分敛散性判定", "多元复合函数求导链式法则", "条件极值拉格朗日乘数法", 
    "二重积分极坐标计算", "三重积分球面坐标变换", "对弧长的曲线积分", 
    "对坐标的曲线积分", "第一类曲面积分", "第二类曲面积分", "高斯公式计算通量", 
    "斯托克斯公式应用题", "周期函数傅里叶展开",
    
    # 大学线代/概统微观概念
    "伴随矩阵求逆公式", "初等变换求逆矩阵", "克拉默法则解方程", "矩阵秩的求法", 
    "施密特正交化过程", "二次型化标准形", "正定矩阵判定条件", "全概率公式计算", 
    "贝叶斯公式应用", "二维连续型随机变量", "边缘分布密度求解", "切比雪夫不等式证明", 
    "极大似然估计步骤", "无偏估计证明"
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
        for kw in GRANULAR_KEYWORDS:
            if kw in db and len(db[kw]) > 0:
                continue
            
            kw, res = await fetch_keyword(client, kw)
            if res:
                db[kw] = res
                added_count += 1
            time.sleep(1) # delay to avoid rate limit
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\nDone! Added {added_count} new granular keywords. Total keywords: {len(db)}")

if __name__ == "__main__":
    asyncio.run(main())
