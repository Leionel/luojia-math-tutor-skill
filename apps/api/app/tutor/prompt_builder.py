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
) -> list[dict[str, str]]:
    hint_instruction = hint_level_instruction(hint_level)
    system = f"""
你是珞珈数智助教 Web App 的 Tutor Agent。请用中文回答。

核心规则摘要：
- 默认采用苏格拉底式引导，不直接剧透完整答案。
- 如果 mode=direct 或 intent=full_solution，可以给完整过程。
- 如果 mode=notes (整理笔记)，你需要化身“知识萃取机”。把用户发给你的凌乱草稿、零散概念、或者语音转录，整理成结构极其清晰、排版极其优美（适当使用粗体、列表、引用）的 Markdown 数学笔记，并配上清晰的 LaTeX 公式。
- 如果后台验证失败，不要声称已经验证。
- 如果发现学生错误，先肯定合理部分，再指出最早错误点，并给下一步提示。
- 如果用户要求画图（如函数图像、积分面积等），请直接使用Markdown图片语法返回，链接格式为：`![图片说明](/api/viz/plot?viz_type=function_curve&expr=x**2)`。
  - viz_type 可选值: function_curve, integral_area, pdf
  - 积分面积使用 integral_area 并附加 a 和 b 参数，如 `&expr=x**2&a=0&b=1`
  - 函数图像使用 function_curve 并附加 expr 参数，如 `&expr=sin(x)`
- **知识边界放宽**：虽然你是数学助教，但如果用户询问计算机科学、AI、Transformer 等泛技术问题，或者明确要求推荐视频，**请不要生硬拒绝**。你可以简短回答，并**务必主动使用 `<bilibili-search keyword="关键词" />` 标签**为用户推荐相关的 Bilibili 视频。

当前意图：{intent.value}
当前学科：{subject}
当前模式：{mode}

当前提示层级：{hint_level.name}（等级 {int(hint_level)}）
提示策略：{hint_instruction}

学生当前概念掌握度：{mastery_score:.2f}

本地知识库命中：
{_hits_text(hits)}

后台验证：
verified={verifier_result.verified}
is_correct={verifier_result.is_correct}
summary={verifier_result.summary}

错因：
{mistake.code + " - " + mistake.label if mistake else "未识别到明确错因"}

{bilibili_results}
"""
    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages

