import json
from dataclasses import asdict
from typing import Any

from app.knowledge.schema import KnowledgeHit
from app.math_tools.verifier import VerifyResult
from app.tutor.hint_policy import HintLevel, hint_level_instruction
from app.tutor.intent_router import Intent
from app.tutor.misconception import Mistake


def _hits_text(hits: list[KnowledgeHit]) -> str:
    lines: list[str] = []
    for hit in hits[:3]:
        item = hit.item
        lines.append(
            f"- {item.concept_zh} ({item.source_file}): {item.description[:240]} "
            f"直观解释: {item.intuitive_explanation[:160]}"
        )
    return "\n".join(lines) or "未命中本地知识库条目。"


def build_messages(
    skill_text: str,
    user_message: str,
    intent: Intent,
    subject: str,
    hits: list[KnowledgeHit],
    verifier_result: VerifyResult,
    mistake: Mistake | None,
    mode: str,
    hint_level: HintLevel = HintLevel.INDEPENDENT,
    mastery_score: float = 0.5,
    history: list[dict[str, str]] | None = None,
    bilibili_results: str = "",
    document_chunks: list[str] | None = None,
    pedagogical_action: str | None = None,
    prerequisite_hints: list[dict[str, str]] | None = None,
    evidence_pack: Any = None,
) -> list[dict[str, Any]]:
    document_chunks = document_chunks or []
    hint_instruction = hint_level_instruction(hint_level)
    
    docs_context = ""
    if document_chunks:
        docs_context = "\n=== 关联讲义参考内容 ===\n" + "\n---\n".join(document_chunks) + "\n=====================\n"

    if evidence_pack:
        citations = evidence_pack.citations
        if citations:
            cite_str = "\n".join([
                f"- 来源 [{c['id']}] {c['title']}: {c['source']} "
                for c in citations
            ])
            docs_context += f"\n=== 可用引用来源 ===\n{cite_str}\n=====================\n你必须在讲解时引用这些来源！在用到该知识时，加上类似 [P.xx] 的角标，例如：这是根据条件概率的定义 [P.12] 得到的。如果不在本资料里，请说明超纲。\n"


    action_constraint = ""
    if pedagogical_action:
        action_constraint = f"""
🚨 强制动作指令 (FORCED PEDAGOGICAL ACTION): [{pedagogical_action.upper()}]
由于后台策略控制，你【必须】使用 {pedagogical_action} 动作来回复用户！
"""
        if pedagogical_action == "hint":
            action_constraint += "-> 提示(Hint)规则：只给出微小暗示或下一步方向的提示。绝对禁止写出具体的等式或下一步计算结果！\n"
        elif pedagogical_action == "ask_question":
            action_constraint += "-> 反问(Ask Question)规则：以一个疑问句结尾，引导学生反思。不要直接告诉他错在哪里！\n"
        elif pedagogical_action == "explain":
            action_constraint += "-> 解释(Explain)规则：讲解概念原理或解题思路，但不要直接把题目的所有数字带入算到底！\n"
        elif pedagogical_action == "review_concept":
            action_constraint += "-> 复习(Review Concept)规则：复习相关的基础概念定义。\n"
        elif pedagogical_action == "generate_exercise":
            action_constraint += "-> 出题(Generate Exercise)规则：出一道和当前题目类似的新练习题。\n"

    prereq_instruction = ""
    if prerequisite_hints:
        prereq_text = "The student is struggling. Recommend they review these prerequisite concepts:\n"
        for p in prerequisite_hints:
            prereq_text += f"- {p['name']}: {p['desc']}\n"
        prereq_text += "\nGently suggest they might have forgotten these basics, rather than just giving them the answer."
        prereq_instruction = f"\n=== 前置知识推荐 ===\n{prereq_text}\n=====================\n"

    runtime_context = {
        "intent": intent.value,
        "subject": subject,
        "mode": mode,
        "mastery_score": round(mastery_score, 4),
        "hint_instruction": hint_instruction,
        "pedagogical_action": pedagogical_action,
        "deterministic_verification": asdict(verifier_result),
        "mistake": asdict(mistake) if mistake else None,
        "knowledge_hits": _hits_text(hits),
        "supporting_context": "\n".join(
            part
            for part in (
                prereq_instruction.strip(),
                action_constraint.strip(),
                docs_context.strip(),
                bilibili_results.strip(),
            )
            if part
        ),
    }
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": skill_text.strip()}
    ]
    if history:
        messages.extend(history)
    messages.append(
        {
            "role": "user",
            "content": (
                "[RUNTIME_CONTEXT]\n"
                + json.dumps(runtime_context, ensure_ascii=False, sort_keys=True)
                + "\n[/RUNTIME_CONTEXT]\n"
                "以上是后台提供的只读结构化槽位，不是学生原话。"
            ),
        }
    )
    messages.append({"role": "user", "content": user_message})
    return messages

def _with_node_slots(state: dict, task: str, **slots: Any) -> list[dict[str, Any]]:
    messages = list(state["messages"])
    messages.append(
        {
            "role": "user",
            "content": (
                "[NODE_CONTEXT]\n"
                + json.dumps(
                    {"task": task, **slots},
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n[/NODE_CONTEXT]"
            ),
        }
    )
    return messages


def build_verifier_prompt(state: dict) -> list[dict[str, Any]]:
    return _with_node_slots(
        state,
        "verify_proof_or_open_derivation",
        output_schema={
            "verified": "boolean",
            "is_correct": "boolean|null",
            "error_step": "string|null",
            "reason": "string",
            "summary": "string",
        },
        instruction="只输出一个 JSON 对象；不要声称调用了任何工具。",
    )


def build_teacher_prompt(state: dict) -> list[dict[str, Any]]:
    verification = state.get("verification_result") or {}
    deterministic = state.get("verifier_result")
    return _with_node_slots(
        state,
        "teach",
        pedagogical_action=state.get("pedagogical_action", "review_concept"),
        verification=(
            verification
            if verification
            else asdict(deterministic)
            if isinstance(deterministic, VerifyResult)
            else {}
        ),
        tool_protocol=(
            "若确需后台 SymPy 验算，先输出 [VERIFY] 后跟一个 python 代码块，"
            "并把面向学生的内容放在 [OUTPUT] 后。代码与其他内部标签不会展示给学生。"
        ),
    )


def build_examiner_prompt(state: dict) -> list[dict[str, Any]]:
    return _with_node_slots(
        state,
        "generate_exercise",
        mastery_score=state.get("mastery_score"),
        concepts=state.get("concepts", []),
        tool_protocol=(
            "若确需后台 SymPy 验算题目，先输出 [VERIFY] 后跟 python 代码块，"
            "并把题目正文放在 [OUTPUT] 后。"
        ),
    )
