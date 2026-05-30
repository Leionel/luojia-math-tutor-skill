"""掌握度更新算法。

规则：
- hint_level=0 独立完成答对 → +0.08
- hint_level>0 有提示答对 → +0.03
- 答错 → -0.06
- 分数区间 [0.0, 1.0]
"""

from dataclasses import dataclass


@dataclass
class MasteryUpdate:
    old_score: float
    new_score: float
    delta: float
    reason: str


def update_mastery(old_score: float, is_correct: bool, hint_level: int = 0) -> MasteryUpdate:
    """计算掌握度更新。

    Args:
        old_score: 当前掌握度 [0.0, 1.0]
        is_correct: 本次是否正确
        hint_level: 提示等级 0-3
    """
    if is_correct and hint_level == 0:
        delta = 0.08
        reason = "独立完成，掌握度上升"
    elif is_correct and hint_level > 0:
        delta = 0.03
        reason = f"在提示等级 {hint_level} 下完成，掌握度小幅上升"
    else:
        delta = -0.06
        reason = "答错，掌握度下降"

    new_score = max(0.0, min(1.0, old_score + delta))
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
