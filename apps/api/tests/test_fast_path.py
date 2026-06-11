from app.tutor.fast_path import (
    VerificationMode,
    generate_opening,
    route_fast_path,
)
from app.tutor.intent_router import Intent


def test_concept_request_uses_one_call_teacher_path():
    route = route_fast_path("什么是导数？", mode="socratic", subject="auto")

    assert route.intent is Intent.CONCEPT
    assert route.subject == "calculus"
    assert route.pedagogical_action == "explain"
    assert route.verification_mode is VerificationMode.NONE
    assert route.requires_policy_fallback is False


def test_clear_student_step_uses_symbolic_verification():
    route = route_fast_path(
        "我算 ∫x^2 dx = x^3，对吗？",
        mode="socratic",
        subject="calculus",
    )

    assert route.intent is Intent.CHECK_STUDENT_STEP
    assert route.verification_mode is VerificationMode.SYMBOLIC
    assert route.pedagogical_action == "ask_question"


def test_complex_proof_uses_llm_verification():
    route = route_fast_path(
        "证明任意有限群的子群阶数整除群的阶数",
        mode="socratic",
        subject="auto",
    )

    assert route.verification_mode is VerificationMode.LLM


def test_exercise_request_routes_to_examiner():
    route = route_fast_path(
        "再出一道条件概率练习题",
        mode="practice",
        subject="probability",
    )

    assert route.intent is Intent.GENERATE_EXERCISE
    assert route.pedagogical_action == "generate_exercise"


def test_opening_is_relevant_but_does_not_repeat_claimed_answer():
    message = "我算 ∫x^2 dx = x^3，对吗？"
    opening = generate_opening(
        route_fast_path(message, mode="socratic", subject="calculus")
    )

    assert "检查" in opening
    assert "x^3" not in opening
    assert "正确" not in opening
    assert "错误" not in opening


def test_opening_templates_cover_all_intents():
    samples = [
        ("什么是条件概率？", "socratic"),
        ("请一步一步解这道题", "socratic"),
        ("给我完整解答", "direct"),
        ("再出一道练习题", "practice"),
    ]

    for message, mode in samples:
        route = route_fast_path(message, mode=mode, subject="auto")
        assert generate_opening(route).strip()
