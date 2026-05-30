from enum import Enum


class Intent(str, Enum):
    CONCEPT = "concept"
    SOLVE_STEP_BY_STEP = "solve_step_by_step"
    CHECK_STUDENT_STEP = "check_student_step"
    FULL_SOLUTION = "full_solution"
    GENERATE_EXERCISE = "generate_exercise"


def route_intent(message: str, mode: str = "socratic") -> Intent:
    lowered = message.lower()
    if mode == "direct" or any(key in message for key in ["完整解答", "标准答案", "直接给", "完整过程"]):
        return Intent.FULL_SOLUTION
    if any(key in message for key in ["类似题", "再出", "练习题", "生成题"]):
        return Intent.GENERATE_EXERCISE
    if any(key in message for key in ["对吗", "这一步", "哪里错", "为什么错", "我算", "我觉得"]):
        return Intent.CHECK_STUDENT_STEP
    if any(key in message for key in ["什么是", "怎么理解", "定义", "直观", "概念"]) or lowered.startswith("what is"):
        return Intent.CONCEPT
    return Intent.SOLVE_STEP_BY_STEP

