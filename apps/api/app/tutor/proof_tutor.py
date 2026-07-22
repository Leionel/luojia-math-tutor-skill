from pydantic import BaseModel, Field
from typing import Optional


class ProofCheckResult(BaseModel):
    step_type: str = Field(description="The type of the current step, e.g., 'use_theorem', 'define_variable', 'logical_deduction'")
    claimed_theorem: Optional[str] = Field(None, description="If a theorem was used, which one?")
    is_valid: bool = Field(description="Is this step logically sound in the context of the proof?")
    missing_reason: Optional[str] = Field(None, description="If invalid or incomplete, what reason is missing? (e.g. 'Need to show sets are disjoint')")
    hint: str = Field(description="A helpful hint to guide the student to the next step or to fix the current step. Never give the direct answer.")


def build_proof_tutor_prompt(state: dict) -> list[dict[str, str]]:
    """Builds a prompt specifically for the Proof Tutoring Protocol."""
    
    system_prompt = """You are an expert Math Tutor specializing in abstract proofs (Real Analysis, Topology, Linear Algebra, etc.).
Your goal is to guide the student through a proof structurally, NOT to give them the final answer or a complete formal verification.

When analyzing a student's proof step:
1. Identify if they are using a specific theorem.
2. Check if the prerequisites for that theorem are met in their context.
3. Check for logic gaps (did they skip a crucial intermediate step?).
4. Check for circular reasoning or definition confusion.

You MUST respond using a structured approach. Do NOT write the rest of the proof for them.
Instead, provide a Socratic hint that points out the missing reason or suggests the next logical target.
"""

    history = state.get("messages", [])
    user_message = state.get("message", "")
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history
    for msg in history:
        messages.append(msg)
        
    # Provide the current context (RAG)
    context_text = ""
    for hit in state.get("hits", []):
        item = getattr(hit, "item", hit)
        context_text += f"Theorem/Concept: {getattr(item, 'concept_zh', '')}\n{getattr(item, 'description', '')}\n\n"
        
    if context_text:
        messages.append({"role": "system", "content": f"Relevant Course Material:\n{context_text}"})

    messages.append({"role": "user", "content": f"Student's current proof step or question: {user_message}"})
    
    return messages
