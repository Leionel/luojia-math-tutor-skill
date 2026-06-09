"""掌握度更新算法 (Bayesian Knowledge Tracing).

规则：
使用 BKT 算法动态更新学生知识点的掌握度 P(L)。
考虑猜测概率 P(G) 和失误概率 P(S)。
"""

from dataclasses import dataclass


@dataclass
class MasteryUpdate:
    old_score: float
    new_score: float
    delta: float
    reason: str


def update_mastery(old_score: float, is_correct: bool, hint_level: int = 0) -> MasteryUpdate:
    """计算掌握度更新 (Bayesian Knowledge Tracing).
    
    Args:
        old_score: 当前掌握度 P(L) [0.0, 1.0]
        is_correct: 本次是否正确
        hint_level: 提示等级 0-3
    """
    p_l = max(0.001, min(0.999, old_score)) # Avoid absolute 0 or 1
    p_s = 0.10
    
    # Dynamic parameters based on hint
    if hint_level == 0:
        p_g = 0.10
        p_t = 0.15
        if is_correct:
            reason = "独立正确解答，掌握度显著上升"
        else:
            reason = "回答错误，掌握度下降"
    elif hint_level == 1:
        p_g = 0.40
        p_t = 0.05
        if is_correct:
            reason = "借助少许提示解答，掌握度小幅上升"
        else:
            reason = "回答错误，掌握度下降"
    else:
        p_g = 0.80
        p_t = 0.00
        if is_correct:
            reason = "在大量提示下解答，掌握度几乎不变"
        else:
            reason = "回答错误，掌握度下降"
            
    if is_correct:
        # P(L|obs) = P(L)(1-S) / [P(L)(1-S) + (1-L)G]
        numerator = p_l * (1 - p_s)
        denominator = numerator + (1 - p_l) * p_g
        p_l_obs = numerator / denominator
    else:
        # P(L|obs) = P(L)S / [P(L)S + (1-L)(1-G)]
        numerator = p_l * p_s
        denominator = numerator + (1 - p_l) * (1 - p_g)
        p_l_obs = numerator / denominator

    new_score = p_l_obs + (1 - p_l_obs) * p_t
    new_score = max(0.0, min(1.0, new_score))
    
    return MasteryUpdate(
        old_score=old_score,
        new_score=new_score,
        delta=round(new_score - old_score, 4),
        reason=reason,
    )


def mastery_label(score: float) -> str:
    """将掌握度分数转为文字标签。"""
    if score >= 0.8:
        return "熟练"
    if score >= 0.6:
        return "掌握"
    if score >= 0.4:
        return "一般"
    if score >= 0.2:
        return "薄弱"
    return "未掌握"
