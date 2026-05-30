import re

from app.knowledge.loader import load_knowledge
from app.knowledge.schema import KnowledgeHit


SUBJECT_HINTS = {
    "calculus": ["高数", "微积分", "导数", "积分", "极限", "洛必达", "函数"],
    "linear_algebra": ["线代", "矩阵", "行列式", "特征值", "特征向量", "线性方程组", "秩"],
    "probability": ["概率", "随机", "分布", "期望", "方差", "条件概率", "独立", "互斥"],
}


def detect_subject(query: str, explicit_subject: str | None = None) -> str | None:
    if explicit_subject and explicit_subject != "auto":
        return explicit_subject
    for subject, hints in SUBJECT_HINTS.items():
        if any(hint in query for hint in hints):
            return subject
    if "∫" in query or "\\int" in query or "lim" in query or "导数" in query:
        return "calculus"
    return None


def _tokens(query: str) -> list[str]:
    parts = re.findall(r"[\w\u4e00-\u9fff]+", query.lower())
    tokens = [part for part in parts if len(part) > 1]
    if "幂函数积分" in query or ("∫" in query and "x" in query):
        tokens.extend(["积分", "不定积分", "原函数", "幂函数"])
    if "条件概率" in query:
        tokens.extend(["条件概率", "乘法定理"])
    if "二阶行列式" in query:
        tokens.extend(["二阶行列式", "行列式"])
    return list(dict.fromkeys(tokens))


def search_knowledge(query: str, subject: str | None = None, limit: int = 5) -> list[KnowledgeHit]:
    detected_subject = detect_subject(query, subject)
    tokens = _tokens(query)
    hits: list[KnowledgeHit] = []
    for item in load_knowledge():
        hay_concept = item.concept_zh.lower()
        hay_prereq = " ".join(item.prerequisite).lower()
        hay_body = " ".join(
            [item.description, item.intuitive_explanation, item.solution, item.source_file]
        ).lower()
        score = 0
        if detected_subject and item.subject == detected_subject:
            score += 2
        for token in tokens:
            if token in hay_concept:
                score += 5
            if token in hay_prereq:
                score += 3
            if token in hay_body:
                score += 1
        if score > 0:
            hits.append(KnowledgeHit(item=item, score=score))
    hits.sort(key=lambda hit: (hit.score, hit.item.concept_zh), reverse=True)
    return hits[:limit]
