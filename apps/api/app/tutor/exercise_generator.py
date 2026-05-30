"""类似题生成模块。"""

import random


# 内置题库 fallback（无 LLM 时使用）
BUILTIN_EXERCISES = {
    "\u5e42\u51fd\u6570\u79ef\u5206": [
        {"text": "\u8ba1\u7b97 $\\int x^3 dx$", "answer": "$\\frac{x^4}{4}+C$", "difficulty": 1},
        {"text": "\u8ba1\u7b97 $\\int x^5 dx$", "answer": "$\\frac{x^6}{6}+C$", "difficulty": 1},
        {"text": "\u8ba1\u7b97 $\\int (3x^2 + 2x) dx$", "answer": "$x^3 + x^2 + C$", "difficulty": 2},
        {"text": "\u8ba1\u7b97 $\\int \\frac{1}{x^2} dx$", "answer": "$-\\frac{1}{x}+C$", "difficulty": 2},
        {"text": "\u8ba1\u7b97 $\\int x^{-1/2} dx$", "answer": "$2\\sqrt{x}+C$", "difficulty": 3},
    ],
    "\u94fe\u5f0f\u6cd5\u5219": [
        {"text": "\u6c42 $\\frac{d}{dx} \\cos(x^2)$ \u7684\u5bfc\u6570", "answer": "$-2x\\sin(x^2)$", "difficulty": 1},
        {"text": "\u6c42 $\\frac{d}{dx} e^{3x}$ \u7684\u5bfc\u6570", "answer": "$3e^{3x}$", "difficulty": 1},
        {"text": "\u6c42 $\\frac{d}{dx} \\ln(x^2+1)$ \u7684\u5bfc\u6570", "answer": "$\\frac{2x}{x^2+1}$", "difficulty": 2},
    ],
    "\u4e0d\u5b9a\u79ef\u5206": [
        {"text": "\u8ba1\u7b97 $\\int \\sin x dx$", "answer": "$-\\cos x + C$", "difficulty": 1},
        {"text": "\u8ba1\u7b97 $\\int e^x dx$", "answer": "$e^x + C$", "difficulty": 1},
        {"text": "\u8ba1\u7b97 $\\int \\frac{1}{1+x^2} dx$", "answer": "$\\arctan x + C$", "difficulty": 2},
    ],
    "\u4e8c\u9636\u884c\u5217\u5f0f": [
        {"text": "\u8ba1\u7b97 $\\begin{vmatrix} 2 & 3 \\\\ 1 & 4 \\end{vmatrix}$", "answer": "$5$", "difficulty": 1},
        {"text": "\u8ba1\u7b97 $\\begin{vmatrix} 5 & -2 \\\\ 3 & 1 \\end{vmatrix}$", "answer": "$11$", "difficulty": 1},
        {"text": "\u8ba1\u7b97 $\\begin{vmatrix} 7 & 1 \\\\ 2 & 3 \\end{vmatrix}$", "answer": "$19$", "difficulty": 1},
        {"text": "\u8ba1\u7b97 $\\begin{vmatrix} a & b \\\\ c & d \\end{vmatrix}$ \u5f53 $a=3,b=2,c=1,d=5$ \u65f6\u7684\u503c", "answer": "$13$", "difficulty": 2},
    ],
    "\u4e09\u9636\u884c\u5217\u5f0f": [
        {"text": "\u8ba1\u7b97 $\\begin{vmatrix} 1 & 2 & 3 \\\\ 4 & 5 & 6 \\\\ 7 & 8 & 9 \\end{vmatrix}$", "answer": "$0$", "difficulty": 2},
        {"text": "\u8ba1\u7b97 $\\begin{vmatrix} 2 & 0 & 1 \\\\ 3 & 1 & 2 \\\\ 1 & 2 & 0 \\end{vmatrix}$", "answer": "$-5$", "difficulty": 2},
    ],
    "\u6761\u4ef6\u6982\u7387": [
        {"text": "\u5df2\u77e5 $P(A)=0.6, P(B|A)=0.5$\uff0c\u6c42 $P(AB)$", "answer": "$0.3$", "difficulty": 1},
        {"text": "\u5df2\u77e5 $P(A)=0.4, P(B)=0.5, P(A|B)=0.3$\uff0c\u6c42 $P(B|A)$", "answer": "$0.375$", "difficulty": 2},
        {"text": "\u5df2\u77e5 $P(A)=0.7, P(B)=0.6, P(AB)=0.42$\uff0c\u5224\u65ad A \u548c B \u662f\u5426\u72ec\u7acb", "answer": "\u662f\uff08$P(AB)=P(A)P(B)=0.42$\uff09", "difficulty": 2},
    ],
    "\u5168\u6982\u7387\u516c\u5f0f": [
        {"text": "\u8bbe $A_1,A_2$ \u662f\u5b8c\u5907\u4e8b\u4ef6\u7ec4\uff0c$P(A_1)=0.6, P(A_2)=0.4$\uff0c$P(B|A_1)=0.2, P(B|A_2)=0.3$\uff0c\u6c42 $P(B)$", "answer": "$0.24$", "difficulty": 1},
        {"text": "\u67d0\u4ea7\u54c1\u7531\u7532\u3001\u4e59\u4e24\u5382\u751f\u4ea7\uff0c\u7532\u5382\u536060%\uff0c\u6b21\u54c1\u73872%\uff1b\u4e59\u5382\u536040%\uff0c\u6b21\u54c1\u73873%\u3002\u6c42\u968f\u673a\u62bd\u53d6\u4e00\u4ef6\u4e3a\u6b21\u54c1\u7684\u6982\u7387", "answer": "$0.024$", "difficulty": 2},
    ],
    "\u5206\u90e8\u79ef\u5206": [
        {"text": "\u8ba1\u7b97 $\\int x e^x dx$", "answer": "$xe^x - e^x + C$", "difficulty": 2},
        {"text": "\u8ba1\u7b97 $\\int \\ln x dx$", "answer": "$x\\ln x - x + C$", "difficulty": 2},
        {"text": "\u8ba1\u7b97 $\\int x \\sin x dx$", "answer": "$-x\\cos x + \\sin x + C$", "difficulty": 2},
    ],
    "\u6781\u9650": [
        {"text": "\u6c42 $\\lim_{x \\to 0} \\frac{\\sin x}{x}$", "answer": "$1$", "difficulty": 1},
        {"text": "\u6c42 $\\lim_{x \\to \\infty} \\frac{3x^2+2x+1}{x^2+5}$", "answer": "$3$", "difficulty": 1},
        {"text": "\u6c42 $\\lim_{x \\to 0} \\frac{1-\\cos x}{x^2}$", "answer": "$\\frac{1}{2}$", "difficulty": 2},
    ],
    "\u77e9\u9635\u4e58\u6cd5": [
        {"text": "\u8ba1\u7b97 $\\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix} \\begin{pmatrix} 2 & 0 \\\\ 1 & 3 \\end{pmatrix}$", "answer": "$\\begin{pmatrix} 4 & 6 \\\\ 10 & 12 \\end{pmatrix}$", "difficulty": 1},
        {"text": "\u8ba1\u7b97 $\\begin{pmatrix} 1 & 0 & 2 \\\\ 0 & 1 & 1 \\end{pmatrix} \\begin{pmatrix} 1 & 1 \\\\ 2 & 0 \\\\ 0 & 1 \\end{pmatrix}$", "answer": "$\\begin{pmatrix} 1 & 3 \\\\ 2 & 1 \\end{pmatrix}$", "difficulty": 2},
    ],
}


def generate_exercise_prompt(concept: str, difficulty: int, mastery_score: float) -> str:
    """生成让 LLM 出题的 prompt。"""
    return (
        f"\u8bf7\u51fa\u4e00\u9053\u5173\u4e8e\u300c{concept}\u300d\u7684\u7ec3\u4e60\u9898\uff0c\u96be\u5ea6\u7b49\u7ea7 {difficulty}/3\u3002"
        f"\u5b66\u751f\u5f53\u524d\u638c\u63e1\u5ea6 {mastery_score:.0%}\u3002"
        f"\u8bf7\u7528 LaTeX \u683c\u5f0f\u8f93\u51fa\u9898\u76ee\u548c\u7b54\u6848\uff0c\u683c\u5f0f\u4e3a\uff1a\n"
        f"\u9898\u76ee\uff1a...\n\u7b54\u6848\uff1a...\n\u8003\u70b9\uff1a{concept}"
    )


def get_fallback_exercises(concept: str, difficulty: int = 2, count: int = 2) -> list[dict]:
    """从内置题库中获取题目（无 LLM 时的 fallback）。"""
    pool = BUILTIN_EXERCISES.get(concept, [])
    if not pool:
        # 尝试模糊匹配
        for key, exercises in BUILTIN_EXERCISES.items():
            if concept in key or key in concept:
                pool = exercises
                break
    if not pool:
        return [{"text": f"\u8bf7\u7ec3\u4e60\u4e00\u9053\u5173\u4e8e\u300c{concept}\u300d\u7684\u9898\u76ee\u3002", "answer": "", "concept": concept, "difficulty": difficulty}]

    filtered = [e for e in pool if e["difficulty"] <= difficulty + 1]
    if not filtered:
        filtered = pool
    selected = random.sample(filtered, min(count, len(filtered)))
    return [{"text": e["text"], "answer": e["answer"], "concept": concept, "difficulty": e["difficulty"]} for e in selected]
