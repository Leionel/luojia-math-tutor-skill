import httpx
import asyncio
import json
import time
import os

# 教科书精细到“小节”级别的关键词
SUBSECTIONS = [
    # 初中小节
    "同底数幂的乘法", "平方差公式", "完全平方公式", "提公因式法", "公式法因式分解",
    "分式的乘除", "二次根式的加减", "一元二次方程的解法", "配方法", "公式法", 
    "一元二次方程的根与系数的关系", "二次函数的图像和性质", "二次函数与一元二次方程",
    "实际问题与二次函数", "反比例函数的图像和性质", "锐角三角函数", "解直角三角形",
    "中心对称与中心对称图形", "圆周角", "垂径定理", "点和圆的位置关系", "直线和圆的位置关系",
    "弧长和扇形面积", "随机事件与概率",
    
    # 高中小节
    "集合的含义与表示", "全称量词与存在量词", "函数的单调性与最值", "函数的奇偶性",
    "指数函数的图像和性质", "对数运算", "对数函数的图像和性质", "任意角的三角函数",
    "同角三角函数的基本关系", "正弦函数的图像与性质", "两角和与差的正弦余弦正切",
    "正弦定理", "余弦定理", "复数的四则运算", "平面向量的数量积", "基本不等式",
    "等差数列的通项公式", "等比数列的前n项和", "空间点直线平面的位置关系", "直线与平面平行的判定",
    "二面角", "空间直角坐标系", "直线的倾斜角与斜率", "圆的标准方程", "椭圆的简单几何性质",
    "双曲线的标准方程", "抛物线的简单几何性质", "排列与组合", "二项式定理", "离散型随机变量及其分布列",
    "正态分布", "导数的几何意义", "导数的计算", "函数的单调性与导数", "函数的极值与导数",
    
    # 大学高数小节
    "数列的极限", "函数的极限", "无穷小与无穷大", "极限运算法则", "两个重要极限",
    "函数的连续性与间断点", "闭区间上连续函数的性质", "导数的概念", "函数的求导法则",
    "高阶导数", "隐函数及由参数方程所确定的函数的导数", "罗尔定理", "拉格朗日中值定理",
    "柯西中值定理", "洛必达法则", "泰勒公式", "函数的单调性与曲线的凹凸性",
    "不定积分的概念与性质", "换元积分法", "分部积分法", "定积分的概念与性质",
    "微积分基本公式", "定积分的换元法和分部积分法", "反常积分", "定积分的元素法",
    "平面图形的面积", "旋转体的体积", "微分方程的基本概念", "可分离变量的微分方程",
    "齐次方程", "一阶线性微分方程", "二阶常系数齐次线性微分方程",
    "向量的混合积", "平面的方程", "空间直线的方程", "多元函数的极限与连续",
    "偏导数", "全微分", "多元复合函数的求导法则", "隐函数的求导公式",
    "方向导数与梯度", "多元函数的极值及其求法", "二重积分的计算法", "二重积分在极坐标下的计算",
    "三重积分的计算", "对弧长的曲线积分", "对坐标的曲线积分", "格林公式及其应用",
    "对面积的曲面积分", "对坐标的曲面积分", "高斯公式", "斯托克斯公式",
    "常数项级数的概念和性质", "正项级数及其审敛法", "交错级数与绝对收敛", "幂级数", "傅里叶级数",
    
    # 大学线代小节
    "行列式的性质", "克拉默法则", "矩阵的乘法", "逆矩阵", "分块矩阵",
    "矩阵的初等变换", "矩阵的秩", "线性方程组的解", "向量组的线性相关性",
    "特征值与特征向量", "相似矩阵", "实对称矩阵的对角化", "二次型及其标准形", "正定二次型",
    
    # 大学概统小节
    "条件概率", "全概率公式与贝叶斯公式", "离散型随机变量及其分布律", "连续型随机变量及其概率密度",
    "边缘分布", "条件分布", "相互独立的随机变量", "两个随机变量的函数的分布",
    "数学期望", "方差", "协方差及相关系数", "切比雪夫不等式", "大数定律", "中心极限定理",
    "抽样分布", "矩估计法", "最大似然估计法", "区间估计", "假设检验的基本思想", "正态总体均值的假设检验"
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
                print(f"[OK] {original_kw} -> {len(results)} videos")
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
        
    print(f"Starting textbook subsection update... Total subsections: {len(SUBSECTIONS)}")
    
    updated_count = 0
    async with httpx.AsyncClient() as client:
        for kw in SUBSECTIONS:
            kw, res = await fetch_keyword(client, kw)
            if res:
                db[kw] = res
                updated_count += 1
            time.sleep(0.5)
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\nDone! Added/Updated {updated_count} textbook subsection keywords. Total keywords in DB: {len(db)}")

if __name__ == "__main__":
    asyncio.run(main())
