import re


CONCEPT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"Fubini|富比尼", "Fubini 定理"),
    (r"二重积分|重积分", "二重积分"),
    (r"\bQR\b|QR\s*算法|QR\s*迭代", "QR 算法"),
    (r"正交相似", "正交相似变换"),
    (r"正交矩阵", "正交矩阵"),
    (r"对称矩阵", "对称矩阵"),
    (r"特征值", "矩阵特征值"),
    (r"Givens|吉文斯", "Givens 旋转"),
    (r"高斯消元", "高斯消元"),
    (r"洛必达", "洛必达法则"),
    (r"分部积分", "分部积分"),
    (r"幂函数.*积分|积分.*幂函数", "幂函数积分"),
    (r"条件概率", "条件概率"),
    (r"正态分布", "正态分布"),
    (r"泰勒展开|Taylor", "泰勒展开"),
    (r"导数", "导数"),
    (r"极限", "极限"),
)


def extract_explicit_concepts(text: str) -> list[str]:
    return [
        concept
        for pattern, concept in CONCEPT_PATTERNS
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]
