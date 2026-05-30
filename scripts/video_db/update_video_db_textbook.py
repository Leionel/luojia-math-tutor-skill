import httpx
import asyncio
import json
import time
import os

# 教科书章节级关键词
TEXTBOOK_CHAPTERS = [
    # 小学教材主要章节 (人教版等综合)
    "四则混合运算", "多边形的面积", "因数与倍数", "分数的意义和性质", "分数的加减法",
    "长方体和正方体", "圆的周长和面积", "百分数", "圆柱与圆锥", "比例", "扇形统计图", 

    # 初中教材章节 (人教版)
    "有理数", "整式的加减", "一元一次方程", "几何图形初步", "相交线与平行线", "实数", 
    "平面直角坐标系", "二元一次方程组", "不等式与不等式组", "三角形的性质与判定", "全等三角形", 
    "轴对称与中心对称", "整式的乘法与因式分解", "分式方程", "二次根式", "勾股定理", 
    "平行四边形", "一次函数", "一元二次方程", "二次函数图像与性质", "旋转与平移", 
    "圆的性质与方程", "概率初步", "反比例函数", "相似三角形", "锐角三角函数", "投影与视图",
    
    # 高中教材章节 (新高考人教A版)
    "集合与常用逻辑用语", "一元二次函数、方程和不等式", "函数的概念与性质", 
    "指数函数与对数函数", "三角函数的概念及恒等变换", "解三角形", "数列及其应用", 
    "一元函数的导数及其应用", "空间向量与立体几何", "直线和圆的方程", "圆锥曲线的方程", 
    "随机事件与概率", "统计与成对数据的统计分析", "计数原理与排列组合", "复数",
    
    # 大学高等数学章节 (同济七版/八版)
    "函数与极限", "导数与微分", "微分中值定理与导数的应用", "不定积分", "定积分", 
    "定积分的应用", "微分方程", "空间解析几何与向量代数", "多元函数微分法及其应用", 
    "重积分", "曲线积分与曲面积分", "无穷级数",
    
    # 大学线性代数章节 (同济六版)
    "行列式", "矩阵及其运算", "矩阵的初等变换与线性方程组", "向量组的线性相关性", 
    "相似矩阵及二次型", "线性空间与线性变换",
    
    # 大学概率论与数理统计章节 (浙大四版/五版)
    "随机事件及其概率", "随机变量及其分布", "多维随机变量及其分布", "随机变量的数字特征", 
    "大数定律及中心极限定理", "样本及抽样分布", "参数估计", "假设检验",
    
    # AI与计算机数学基础章节
    "神经网络基础数学", "卷积神经网络CNN", "循环神经网络RNN", "注意力机制与Transformer", 
    "生成对抗网络GAN", "强化学习数学基础", "最优化算法理论", "图论初步", "离散数学集合与图"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": "buvid3=D44F2E1E-B9AB-7B93-DE44-24E48DF42E4349141infoc;"
}

async def fetch_keyword(client, original_kw):
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
    
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        db = {}
        
    print(f"Loaded existing DB. Starting textbook chapter update...")
    
    updated_count = 0
    async with httpx.AsyncClient() as client:
        for kw in TEXTBOOK_CHAPTERS:
            kw, res = await fetch_keyword(client, kw)
            if res:
                db[kw] = res
                updated_count += 1
            time.sleep(0.5) # delay to avoid rate limit
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\nDone! Added/Updated {updated_count} textbook chapter keywords. Total keywords: {len(db)}")

if __name__ == "__main__":
    asyncio.run(main())
