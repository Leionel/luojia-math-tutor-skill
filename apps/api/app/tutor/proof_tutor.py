"""Proof tutoring reuses the resolved policy and upstream review."""
from app.tutor.prompt_builder import _with_node_slots

def build_proof_tutor_prompt(state: dict) -> list[dict]:
    return _with_node_slots(
        state, "proof_tutoring",
        verification=state.get("verification_result") or {},
        instruction=(
            "依据LLM审查给证明建议，明确区分已确认正确、前提未交代、发现错误、暂无法判断。"
            "指出最早可确认的逻辑问题和下一步，不把LLM意见称为严格验证。"
            "遵循resolved_policy的披露程度；默认提示不代写证明，明确完整请求可给全程。"
        ),
    )
