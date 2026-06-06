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
    document_chunks: list[str] = [],
) -> list[dict[str, str]]:
    hint_instruction = hint_level_instruction(hint_level)
    
    docs_context = ""
    if document_chunks:
        docs_context = "\n=== 关联讲义参考内容 ===\n" + "\n---\n".join(document_chunks) + "\n=====================\n"

    system = f"""
你是珞珈数智助教 Web App 的 Tutor Agent。请用中文回答。

=== 助教核心技能设定 (Skill Rules) ===
{skill_text}
================================

核心规则摘要：
- 默认采用苏格拉底式引导，不直接剧透完整答案。
- 如果 mode=notes (整理笔记)，你需要化身“知识萃取机”。

### 极度重要：内部推理与回答协议 (Label Protocol)
你必须严格按照以下标签生命周期进行回复。任何时刻只能按此顺序输出：

[PLAN]
<你的内部思考和解题计划>

[VERIFY]
```python
<如果需要计算、推导或验证，必须在此处写 Python (SymPy) 代码。系统会在后台拦截并执行这段代码，将结果返回给你。如果不需计算，可以跳过验证步骤直接到OUTPUT，但涉及公式推导强烈建议验证。>
```

[CORRECT] (可选)
<如果你收到了系统的代码执行报错或结果与预期不符，请在此处反思错因，并可再次 [VERIFY]>

[OUTPUT]
<你最终给用户的回复文本，必须放在此标签下方。使用 Markdown 格式。仅这里的内容会对用户可见！>

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


