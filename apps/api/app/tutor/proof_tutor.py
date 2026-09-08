import json
from pydantic import BaseModel, Field
from typing import Optional


class ProofCheckResult(BaseModel):
    step_type: str = Field(description="The type of the current step, e.g., 'use_theorem', 'define_variable', 'logical_deduction'")
    claimed_theorem: Optional[str] = Field(None, description="If a theorem was used, which one?")
    is_valid: bool = Field(description="Is this step logically sound in the context of the proof?")
    missing_reason: Optional[str] = Field(None, description="If invalid or incomplete, what reason is missing? (e.g. 'Need to show sets are disjoint')")
    hint: str = Field(description="A helpful hint to guide the student to the next step or to fix the current step. Never give the direct answer.")


def build_proof_tutor_prompt(state: dict) -> list[dict[str, str]]:
    """Add proof-specific slots without replacing the SKILL.md system source."""
    messages = list(state.get("messages", []))
    context = []
    for hit in state.get("hits", []):
        item = getattr(hit, "item", hit)
        context.append(
            {
                "concept": getattr(item, "concept_zh", ""),
                "description": getattr(item, "description", ""),
            }
        )
    messages.append(
        {
            "role": "user",
            "content": (
                "[NODE_CONTEXT]\n"
                + json.dumps(
                    {
                        "task": "proof_tutoring",
                        "relevant_material": context,
                        "verification": state.get("verification_result") or {},
                        "instruction": (
                            "检查所用定理的前提、逻辑缺口与循环论证；"
                            "按 SKILL.md 的启发式规则给下一步提示，不代写完整证明。"
                        ),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n[/NODE_CONTEXT]"
            ),
        }
    )
    return messages
