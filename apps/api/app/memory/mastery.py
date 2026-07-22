"""掌握度更新算法 (Bayesian Knowledge Tracing).

规则：
使用 BKT 算法动态更新学生知识点的掌握度 P(L)。
考虑猜测概率 P(G) 和失误概率 P(S)。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LearningEvent:
    event_type: str  # e.g. "check_step", "explain"
    correct: bool
    hint_level: int
    difficulty: int = 3
    error_type: Optional[str] = None  # "concept_confusion", "calculation_error", "logic_gap", etc.
    time_spent: Optional[int] = None

@dataclass
class MasteryUpdate:
    old_score: float
    new_score: float
    delta: float
    reason: str


def update_mastery(
    old_score: float,
    event: LearningEvent | bool | None = None,
    hint_level: int = 0,
    *,
    is_correct: bool | None = None,
    difficulty: int = 3,
    error_type: Optional[str] = None,
    time_spent: Optional[int] = None,
) -> MasteryUpdate:
    """计算掌握度更新 (Bayesian Knowledge Tracing).

    ``LearningEvent`` 是当前接口。为了兼容旧的调用方，也接受
    ``update_mastery(score, is_correct=True, hint_level=0)`` 和位置参数形式。

    Args:
        old_score: 当前掌握度 P(L) [0.0, 1.0]
        event: 学习事件，或旧接口中的 is_correct 布尔值
        hint_level: 旧接口中的提示等级
        is_correct: 旧接口中的正确性参数
    """
    if isinstance(event, LearningEvent):
        if is_correct is not None:
            raise TypeError("event and is_correct cannot be used together")
        learning_event = event
    elif isinstance(event, bool):
        if is_correct is not None:
            raise TypeError("event and is_correct cannot be used together")
        learning_event = LearningEvent(
            event_type="check_step",
            correct=event,
            hint_level=hint_level,
            difficulty=difficulty,
            error_type=error_type,
            time_spent=time_spent,
        )
    elif event is None and is_correct is not None:
        learning_event = LearningEvent(
            event_type="check_step",
            correct=is_correct,
            hint_level=hint_level,
            difficulty=difficulty,
            error_type=error_type,
            time_spent=time_spent,
        )
    else:
        raise TypeError(
            "update_mastery expects a LearningEvent or the legacy is_correct argument"
        )

    event = learning_event
    p_l = max(0.001, min(0.999, old_score)) # Avoid absolute 0 or 1
    p_s = 0.10

    # Difficulty adjustment (1-5, higher is harder). Normalizes base probabilities.
    difficulty_factor = max(1, min(5, event.difficulty)) / 3.0

    # Dynamic parameters based on hint and difficulty
    if event.hint_level == 0:
        base_p_g = 0.10
        p_t = 0.15
        if event.correct:
            reason = "独立正确解答，掌握度显著上升"
        else:
            reason = "回答错误，掌握度下降"
            if event.error_type:
                reason = f"回答错误({event.error_type})，掌握度下降"
    elif event.hint_level == 1:
        base_p_g = 0.40
        p_t = 0.05
        if event.correct:
            reason = "借助少许提示解答，掌握度小幅上升"
        else:
            reason = "回答错误，掌握度下降"
            if event.error_type:
                reason = f"回答错误({event.error_type})，掌握度下降"
    else:
        base_p_g = 0.80
        p_t = 0.00
        if event.correct:
            reason = "在大量提示下解答，掌握度几乎不变"
        else:
            reason = "回答错误，掌握度下降"
            if event.error_type:
                reason = f"回答错误({event.error_type})，掌握度下降"

    p_g = min(0.95, base_p_g / difficulty_factor)

    if event.correct:
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
