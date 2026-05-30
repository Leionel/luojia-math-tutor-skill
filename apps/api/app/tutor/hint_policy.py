"""提示层级决策模块。

根据掌握度、连续错误次数和用户请求决定提示层级。
"""

from enum import IntEnum


class HintLevel(IntEnum):
    INDEPENDENT = 0   # 学生独立思考，只给方向性引导
    LIGHT_HINT = 1    # 轻提示：指出使用什么方法/定理
    FORMULA_HINT = 2  # 公式提示：给出关键公式
    NEAR_ANSWER = 3   # 接近答案：只差最后一步


def decide_hint_level(
    mastery_score: float,
    consecutive_errors: int,
    user_requested_hint: bool,
    mode: str = "socratic",
) -> HintLevel:
    """决定提示层级。

    Args:
        mastery_score: 当前概念掌握度 [0.0, 1.0]
        consecutive_errors: 同一概念连续错误次数
        user_requested_hint: 用户是否主动要求提示
        mode: 教学模式 socratic/direct/practice
    """
    # direct 模式直接给答案级提示
    if mode == "direct":
        return HintLevel.NEAR_ANSWER

    # 用户主动要求提示，至少给 LIGHT_HINT
    base = HintLevel.LIGHT_HINT if user_requested_hint else HintLevel.INDEPENDENT

    # 连续错误次数升级提示
    if consecutive_errors >= 3:
        base = max(base, HintLevel.NEAR_ANSWER)
    elif consecutive_errors >= 2:
        base = max(base, HintLevel.FORMULA_HINT)
    elif consecutive_errors >= 1:
        base = max(base, HintLevel.LIGHT_HINT)

    # 掌握度低时升级提示
    if mastery_score < 0.2:
        base = max(base, HintLevel.FORMULA_HINT)
    elif mastery_score < 0.4:
        base = max(base, HintLevel.LIGHT_HINT)

    return HintLevel(min(base, HintLevel.NEAR_ANSWER))


def hint_level_instruction(level: HintLevel) -> str:
    """根据提示层级生成 prompt 指令片段。"""
    instructions = {
        HintLevel.INDEPENDENT: (
            "学生掌握度较高，只给方向性引导，不给具体公式或步骤。"
        ),
        HintLevel.LIGHT_HINT: (
            "给出使用的方法或定理名称，但不展开具体公式。"
        ),
        HintLevel.FORMULA_HINT: (
            "学生多次出错或掌握度较低，给出关键公式，并引导代入。"
        ),
        HintLevel.NEAR_ANSWER: (
            "学生反复出错或主动要求完整解答，可以给出几乎完整的过程，"
            "只留最后一个简单计算让学生完成。"
        ),
    }
    return instructions.get(level, instructions[HintLevel.INDEPENDENT])
