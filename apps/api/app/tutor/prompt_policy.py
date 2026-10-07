"""One resolved teaching policy, shared by all generation nodes."""
from pathlib import Path
from app.tutor.hint_policy import HintLevel
from app.tutor.intent_router import Intent

REFERENCE_FILES = ("interactive-tutoring.md", "math-tools-guidelines.md", "knowledge-base-usage.md", "visual-artifacts.md")
PROMPT_VERSION = "teaching-v2.7"

def load_teaching_prompt(skill_file: Path) -> str:
    sections = [skill_file.read_text(encoding="utf-8")]
    for name in REFERENCE_FILES:
        path = skill_file.parent / "references" / name
        sections.append(f"\n[教学规范：{name}]\n{path.read_text(encoding='utf-8')}")
    return "\n".join(sections)

def resolve_teaching_policy(intent: Intent, mode: str, hint_level: HintLevel,
                            action: str | None, case: dict | None = None) -> dict:
    full = intent == Intent.FULL_SOLUTION or (mode == "direct" and intent != Intent.GENERATE_EXERCISE)
    if full:
        action = "explain"
    elif intent == Intent.GENERATE_EXERCISE:
        action = "generate_exercise"
    elif not action:
        from app.tutor.intent_router import ACTION_BY_INTENT
        action = ACTION_BY_INTENT[intent].value
    return {
        "action": action,
        "disclosure": "full" if full else "scaffolded",
        "hint_level": int(hint_level),
        "case_default": (case or {}).get("disclosure_policy", "scaffolded"),
        "instruction": (
            "学生明确要求完整解答。给出完整过程与结论，注明前提和误差；不强制留最后一步或反问。"
            if full else
            "按当前任务直接回答。解题默认推进一至两个关键步骤；提示等级0给方向、1给方法、"
            "2给关键公式、3给主要过程。概念定义可完整给出。纠错先说明审查状态与最早问题，"
            "再给一个可执行的修改建议；仅当需要学生补充或练习时提一个具体问题。"
            "出题时只给题目与必要条件，答案留到学生作答或明确索取后。"
        ),
    }
