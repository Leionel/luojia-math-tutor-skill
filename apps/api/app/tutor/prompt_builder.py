from app.knowledge.schema import KnowledgeHit
from app.math_tools.verifier import VerifyResult
from app.tutor.hint_policy import HintLevel, hint_level_instruction
from app.tutor.intent_router import Intent
from app.tutor.misconception import Mistake
from langchain_core.messages import SystemMessage


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
    document_chunks: list[str] = [],
    pedagogical_action: str | None = None,
) -> list[dict[str, str]]:
    hint_instruction = hint_level_instruction(hint_level)
    
    docs_context = ""
    if document_chunks:
        docs_context = "\n=== 关联讲义参考内容 ===\n" + "\n---\n".join(document_chunks) + "\n=====================\n"

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

    system = f"""
你是珞珈数智助教 Web App 的 Tutor Agent。请用中文回答。

=== 助教核心技能设定 (Skill Rules) ===
{skill_text}
================================

核心规则摘要：
- 默认采用苏格拉底式引导，不直接剧透完整答案。
- 如果 mode=notes (整理笔记)，你需要化身“知识萃取机”。

### 🚨 极度重要：内部推理与防暴雷协议 (Zero-Leakage & Action Protocol)
真实导师的核心素养是“忍住不直接给答案”。你必须严格按照以下标签生命周期进行回复：

[PLAN]
在正式回复前，你必须进行内部推理（该部分用户不可见）：
1. 真实答案验证：当前学生解答到了哪一步？最终正确答案是什么？
2. 进度与错因定位：学生卡在哪了？逻辑漏洞是什么？
3. 知识防暴雷：为了让他自己顿悟，**我接下来绝对不能写出来的数字或公式是什么？**（请明确列出黑名单）。
4. 教学策略判定：如果系统指定了强制动作指令，必须选定该指令。否则选一：hint/ask_question/explain/review_concept/generate_exercise。
5. 引导方案：我将如何通过该策略引导他？

[VERIFY]
```python
<如果需要后台计算或验证，必须写 Python/SymPy 代码。系统会拦截并返回执行结果。若无需计算可跳过。>
```

[CORRECT] (可选)
<如果收到代码报错或结果不符，在此处反思错因，并可再次 [VERIFY]>

[OUTPUT]
<你最终给用户的回复文本，使用 Markdown 格式。仅这里的内容会对用户可见！>
⚠️ 警告：在 [OUTPUT] 中，你必须执行你选择的策略，如果存在【强制动作指令】，你必须遵守！
**绝对禁止**直接输出你在第3步列出的“防暴雷黑名单”内容。不要破坏学生的探索过程！

{action_constraint}

{docs_context}

当前意图：{intent.value}
当前学科：{subject}
当前模式：{mode}
学生当前概念掌握度：{mastery_score:.2f}

本地知识库命中：
{_hits_text(hits)}

{bilibili_results}
"""
    messages = [{"role": "system", "content": system.strip()}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages

def build_verifier_prompt(state: dict) -> list:
    sys_msg = """你是一个冷酷的数学验证专家 (Verifier)。
你的唯一任务是判断学生的解答是否正确，以及出错在第几步。
你可以使用 sandbox 工具调用 python 来运算。
你的最终输出必须是明确的判定结果。不要对学生说话。"""
    
    # Return messages formatted for the verifier model
    messages = [SystemMessage(content=sys_msg)] + state["messages"]
    return messages

def build_teacher_prompt(state: dict) -> list:
    action = state.get("pedagogical_action", "review_concept")
    ver_res = state.get("verification_result", {})
    
    sys_msg = f"""你是一个友善的高数助教。
当前策略: {action}
裁判的验证结果: {ver_res}

【绝密指令】：永远不要直接向学生透露答案！只能基于验证结果，给予启发式引导。"""

    messages = [SystemMessage(content=sys_msg)] + state["messages"]
    return messages

def build_examiner_prompt(state: dict) -> list:
    sys_msg = """你是一个出题官。请基于学生的掌握度，给出一道新题目。"""
    messages = [SystemMessage(content=sys_msg)] + state["messages"]
    return messages
