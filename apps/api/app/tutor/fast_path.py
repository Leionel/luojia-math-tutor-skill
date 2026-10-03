from dataclasses import dataclass
from enum import Enum

from app.knowledge.search import detect_subject
from app.search.policy import is_external_fact_question
from app.tutor.intent_router import ACTION_BY_INTENT, Intent, route_intent_decision


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


_OBJECTIVE_BY_INTENT = {
    Intent.CONCEPT: "理解概念的核心含义与适用场景",
    Intent.SOLVE_STEP_BY_STEP: "识别题型并完成下一步推导",
    Intent.CHECK_STUDENT_STEP: "核对当前步骤并定位需要调整之处",
    Intent.FULL_SOLUTION: "梳理解题条件并完成关键推导",
    Intent.GENERATE_EXERCISE: "通过同类练习巩固当前考点",
    Intent.PROOF_HINT: "定位证明中的逻辑缺口并给出下一步提示",
}


def learning_objective_for_intent(intent: Intent) -> str:
    return _OBJECTIVE_BY_INTENT[intent]

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


def verification_mode_for(message: str, intent: Intent) -> VerificationMode:
    """Use the same verification policy after either routing path."""
    if is_external_fact_question(message):
        return VerificationMode.NONE
    if intent is Intent.PROOF_HINT or any(marker in message.lower() for marker in _PROOF_MARKERS):
        return VerificationMode.LLM
    elif intent is Intent.CHECK_STUDENT_STEP and any(
        marker in message for marker in _SYMBOLIC_MARKERS
    ):
        return VerificationMode.SYMBOLIC
    return VerificationMode.NONE


def route_fast_path(message: str, mode: str, subject: str) -> FastRoute:
    intent_decision = route_intent_decision(message, mode)
    detected_subject = detect_subject(message, subject) or subject
    factual = is_external_fact_question(message)
    intent = Intent.CONCEPT if factual else intent_decision.intent
    verification_mode = verification_mode_for(message, intent)

    return FastRoute(
        intent=intent,
        subject=detected_subject,
        pedagogical_action=ACTION_BY_INTENT[intent].value,
        learning_objective=learning_objective_for_intent(intent),
        verification_mode=verification_mode,
        confidence=0.95 if factual else intent_decision.confidence,
        requires_policy_fallback=False if factual else intent_decision.uncertain,
    )


def generate_opening(route: FastRoute) -> str:
    if route.requires_policy_fallback:
        return "我先结合上下文确认你想完成的任务。"
    openings = {
        Intent.CONCEPT: "我们先抓住这个概念解决的核心问题，再看它怎样用于题目。",
        Intent.SOLVE_STEP_BY_STEP: "我们先确定题型和第一步可用的规则，再继续推进。",
        Intent.CHECK_STUDENT_STEP: "我先检查你这一步使用的规则，再一起定位需要调整的位置。",
        Intent.FULL_SOLUTION: "我先整理题目的已知条件和目标，再按关键步骤展开。",
        Intent.GENERATE_EXERCISE: "我会围绕当前考点给你一道同难度练习，并保留独立作答空间。",
        Intent.PROOF_HINT: "我先检查证明的结构和已用定理，再给你一个不剧透结论的下一步提示。",
    }
    return openings[route.intent]
