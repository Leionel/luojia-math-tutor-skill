"""Bounded delivery rules; passing is never a mathematical validity verdict."""
import re
from dataclasses import dataclass

GUARD_VERSION = "delivery-v2"


@dataclass(frozen=True)
class DeliveryCheck:
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.violations


def guard_report(status: str, violations=(), repair_count: int = 0, *, enabled=True) -> dict:
    return {"version": GUARD_VERSION, "scope": "delivery_rules_only", "status": status,
            "rule_ids": list(violations), "repair_count": repair_count, "enabled": enabled}


class AnswerDeliveryError(RuntimeError):
    def __init__(self, report: dict):
        self.report = report
        self.code = "answer_guard_unavailable" if report["status"] == "unavailable" else "answer_withheld"
        super().__init__("回答交付检查暂不可用，本轮没有交付正文。" if self.code == "answer_guard_unavailable"
                         else "回答未通过交付检查，本轮没有交付正文，请调整问题后重试。")


def _assertion_text(text: str) -> str:
    # Examples and quotations are data, not assertions by the assistant.
    text = re.sub(r"```[^\n]*\n.*?(?:```|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"(?m)^\s*>.*$", "", text)
    text = re.sub(r"`[^`\n]+`", "", text)
    return re.sub(r'“[^”]*”|「[^」]*」|『[^』]*』|"[^"\n]*"|(?<!\w)\x27[^\x27\n]+\x27(?!\w)', "", text)


def _positive(text: str, match: re.Match) -> bool:
    prefix = re.split(r"[。！？.!?；;\n，,]", text[:match.start()])[-1][-40:]
    return not re.search(r"不|未|没有|并非|不能|尚未|\bnot\b|\bnever\b|didn't|haven't", prefix + match.group(), re.I)


def _claims(text: str, pattern: str) -> bool:
    return any(_positive(text, match) for match in re.finditer(pattern, text, re.I))


def answer_requested(message: str) -> bool:
    return _claims(message, r"(?:给出?|提供|附上?|带|含)(?:完整)?(?:答案|解答)|答案(?:是什么|呢)|with\s+(?:an?\s+)?(?:answer|solution)")


def check_delivery(text: str, *, exercise: bool = False, allow_answer: bool = False,
                   execution_succeeded: bool = False, tool_evidence=None) -> DeliveryCheck:
    """High precision checks of explicit claims/sections, not all semantic leaks.

    Unlabelled answers, indirect claims and mathematical correctness require
    separate evaluation; this contract does not pretend to cover them.
    """
    violations = []
    if not text.strip():
        violations.append("empty_body")
    assertions = _assertion_text(text)
    evidence = tool_evidence or []
    if evidence and not any(item.get("status") == "succeeded" for item in evidence) and _claims(assertions, r"(?:工具|求导|数值计算)(?:已|已经)?(?:成功|完成|验证通过)|经(?:工具|数值计算)验证"):
        violations.append("tool_result_contradiction")
    if any((item.get("data") or {}).get("evidence_scope") == "quadrature_error_estimate" for item in evidence) and _claims(assertions, r"积分(?:结果|误差)[^。\n]{0,15}(?:严格保证|严格验证|已证明)"):
        violations.append("integration_scope_claim")
    if re.search(r"\[(?:PLAN|VERIFY|CORRECT|OUTPUT|TOOL_RESULT|RUNTIME_CONTEXT|NODE_CONTEXT)\]", assertions, re.I):
        violations.append("internal_protocol")
    if _claims(assertions, r"(?:已(?:经)?(?:成功)?(?:运行|执行)|(?:我|我们)(?:运行|执行)了)(?:了)?\s*(?:你的|您(?:的)?|学生的)(?:完整)?(?:Python\s*)?(?:代码|程序|作业)|\b(?:I|we)\s+(?:have\s+)?(?:executed|ran|run)\s+your\s+(?:code|program)"):
        violations.append("student_code_execution_claim")
    if not execution_succeeded and _claims(assertions, r"(?:已(?:经)?(?:成功)?(?:运行|执行)|(?:我|我们)(?:运行|执行)了)(?:了)?\s*(?:计算|验算|验证)?(?:代码|程序)|\b(?:I|we)\s+(?:have\s+)?(?:executed|ran|run)\s+(?:the\s+)?(?:code|program)"):
        violations.append("execution_without_evidence")
    if _claims(assertions, r"(?:全部|所有|整段|整个)(?:的)?(?:结论|推导|答案|回答|步骤)[^。！？\n]{0,30}(?:验证通过|验证无误|严格(?:数学)?验证|数学证明|确定性验证)|(?:工具|代码)(?:运行|执行)成功[^。\n]{0,20}(?:证明|保证)(?:全部|所有|整段|整个)(?:结论|答案|推导)(?:正确|无误)"):
        violations.append("whole_answer_validation_claim")
    if exercise and not allow_answer:
        for match in re.finditer(r"(?im)^\s*(?:#{1,6}\s*)?(?:(?:参考|标准|完整)\s*)?(?:答案|解答|解析|answer|solution)\s*[:：]\s*(.*)$|(?:参考答案|标准答案|最终答案)(?:是|为)\s*([^\n]+)", assertions):
            payload = next((part for part in match.groups() if part is not None), "").strip()
            if payload and not re.fullmatch(r"[_…\.\s]+|略|待填写|由你填写|暂不提供", payload) and _positive(assertions, match):
                violations.append("exercise_answer_disclosure")
                break
    return DeliveryCheck(tuple(dict.fromkeys(violations)))


def check_root_contract(report: dict, output: str) -> dict:
    """Read-only contract check of a deterministic receipt, never LLM repair."""
    valid = (isinstance(report.get("complete"), bool)
             and report.get("status") in {"supported", "contradicted", "inconclusive", "tool_error"}
             and isinstance(report.get("summary"), str) and bool(report["summary"].strip())
             and bool(output.strip())
             and not (report["complete"] and report["status"] != "supported"))
    if not valid:
        raise AnswerDeliveryError(guard_report("withheld", ["root_receipt_contract"]))
    return guard_report("passed")
