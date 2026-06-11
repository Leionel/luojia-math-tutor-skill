from dataclasses import dataclass
from enum import Enum

from app.knowledge.search import detect_subject
from app.tutor.intent_router import Intent, route_intent


class VerificationMode(str, Enum):
    NONE = "none"
    SYMBOLIC = "symbolic"
    LLM = "llm"


@dataclass(frozen=True)
class FastRoute:
    intent: Intent
    subject: str
    pedagogical_action: str
    learning_objective: str
    verification_mode: VerificationMode
    confidence: float
    requires_policy_fallback: bool


_ACTION_BY_INTENT = {
    Intent.CONCEPT: "explain",
    Intent.SOLVE_STEP_BY_STEP: "hint",
    Intent.CHECK_STUDENT_STEP: "ask_question",
    Intent.FULL_SOLUTION: "explain",
    Intent.GENERATE_EXERCISE: "generate_exercise",
}

_OBJECTIVE_BY_INTENT = {
    Intent.CONCEPT: "理解概念的核心含义与适用场景",
    Intent.SOLVE_STEP_BY_STEP: "识别题型并完成下一步推导",
    Intent.CHECK_STUDENT_STEP: "核对当前步骤并定位需要调整之处",
    Intent.FULL_SOLUTION: "梳理解题条件并完成关键推导",
    Intent.GENERATE_EXERCISE: "通过同类练习巩固当前考点",
}

_PROOF_MARKERS = (
    "证明",
    "推导",
    "必要性",
    "充分性",
    "当且仅当",
    "反例",
    "prove",
    "proof",
)

_SYMBOLIC_MARKERS = (
    "=",
    "∫",
    "\\int",
    "lim",
    "求导",
    "导数",
    "对吗",
    "正确吗",
)


def route_fast_path(message: str, mode: str, subject: str) -> FastRoute:
    intent = route_intent(message, mode)
    detected_subject = detect_subject(message, subject) or subject

    if any(marker in message.lower() for marker in _PROOF_MARKERS):
        verification_mode = VerificationMode.LLM
    elif intent is Intent.CHECK_STUDENT_STEP and any(
        marker in message for marker in _SYMBOLIC_MARKERS
    ):
        verification_mode = VerificationMode.SYMBOLIC
    else:
        verification_mode = VerificationMode.NONE

    stripped = message.strip()
    confidence = 0.55 if len(stripped) < 3 else 0.9

    return FastRoute(
        intent=intent,
        subject=detected_subject,
        pedagogical_action=_ACTION_BY_INTENT[intent],
        learning_objective=_OBJECTIVE_BY_INTENT[intent],
        verification_mode=verification_mode,
        confidence=confidence,
        requires_policy_fallback=confidence < 0.7,
    )


def generate_opening(route: FastRoute) -> str:
    openings = {
        Intent.CONCEPT: "我们先抓住这个概念解决的核心问题，再看它怎样用于题目。",
        Intent.SOLVE_STEP_BY_STEP: "我们先确定题型和第一步可用的规则，再继续推进。",
        Intent.CHECK_STUDENT_STEP: "我先检查你这一步使用的规则，再一起定位需要调整的位置。",
        Intent.FULL_SOLUTION: "我先整理题目的已知条件和目标，再按关键步骤展开。",
        Intent.GENERATE_EXERCISE: "我会围绕当前考点给你一道同难度练习，并保留独立作答空间。",
    }
    return openings[route.intent]
