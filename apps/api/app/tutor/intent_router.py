from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    CONCEPT = "concept"
    SOLVE_STEP_BY_STEP = "solve_step_by_step"
    CHECK_STUDENT_STEP = "check_student_step"
    FULL_SOLUTION = "full_solution"
    GENERATE_EXERCISE = "generate_exercise"
    PROOF_HINT = "proof_hint"


class PedagogicalAction(str, Enum):
    HINT = "hint"
    ASK_QUESTION = "ask_question"
    EXPLAIN = "explain"
    REVIEW_CONCEPT = "review_concept"
    GENERATE_EXERCISE = "generate_exercise"
    PROVIDE_HINT = "provide_hint"


ACTION_BY_INTENT: dict[Intent, PedagogicalAction] = {
    Intent.CONCEPT: PedagogicalAction.EXPLAIN,
    Intent.SOLVE_STEP_BY_STEP: PedagogicalAction.HINT,
    Intent.CHECK_STUDENT_STEP: PedagogicalAction.ASK_QUESTION,
    Intent.FULL_SOLUTION: PedagogicalAction.EXPLAIN,
    Intent.GENERATE_EXERCISE: PedagogicalAction.GENERATE_EXERCISE,
    Intent.PROOF_HINT: PedagogicalAction.PROVIDE_HINT,
}

if set(ACTION_BY_INTENT) != set(Intent):
    raise RuntimeError("Every Intent must have exactly one default action.")


@dataclass(frozen=True)
class IntentDecision:
    intent: Intent
    confidence: float
    uncertain: bool
    matched_intents: tuple[Intent, ...]


_MARKERS: dict[Intent, tuple[str, ...]] = {
    Intent.FULL_SOLUTION: ("完整解答", "标准答案", "直接给", "完整过程", "算到底"),
    Intent.GENERATE_EXERCISE: ("类似题", "再出", "练习题", "生成题", "来一道"),
    Intent.PROOF_HINT: ("证明", "怎么证", "证法", "推导", "证一下"),
    Intent.CHECK_STUDENT_STEP: (
        "对吗", "这一步", "哪里错", "为什么错", "我算", "我觉得", "帮我检查", "验算",
    ),
    Intent.CONCEPT: ("什么是", "怎么理解", "定义", "直观", "概念", "what is"),
}

_NEGATIONS = ("不要", "不需要", "别", "无需", "先不")


def _is_negated(text: str, marker: str) -> bool:
    index = text.find(marker)
    if index < 0:
        return False
    prefix = text[max(0, index - 5) : index]
    return any(negative in prefix for negative in _NEGATIONS)


def route_intent_decision(message: str, mode: str = "socratic") -> IntentDecision:
    text = message.strip().lower()
    if mode == "direct":
        return IntentDecision(Intent.FULL_SOLUTION, 0.99, False, (Intent.FULL_SOLUTION,))

    matched: list[Intent] = []
    for intent, markers in _MARKERS.items():
        if any(marker in text and not _is_negated(text, marker) for marker in markers):
            matched.append(intent)

    if not matched:
        math_signal = any(
            marker in text
            for marker in ("=", "∫", "\\int", "lim", "矩阵", "概率", "函数", "求")
        )
        confidence = 0.78 if math_signal else 0.45
        return IntentDecision(
            Intent.SOLVE_STEP_BY_STEP,
            confidence,
            confidence < 0.7,
            (),
        )

    intent = matched[0]
    confidence = 0.93 if len(matched) == 1 else 0.58
    return IntentDecision(intent, confidence, len(matched) > 1, tuple(matched))


def route_intent(message: str, mode: str = "socratic") -> Intent:
    return route_intent_decision(message, mode).intent
