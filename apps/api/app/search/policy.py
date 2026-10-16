"""Bounded search routing; explicit off always wins over automatic freshness."""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchDecision:
    enabled: bool
    reason: str
    factual: bool


def is_external_fact_question(message: str) -> bool:
    text = message.lower()
    news = re.search(r"最新|新闻|报道|发布|宣布|最近.{0,20}(?:研究|论文|进展)|今年.{0,20}(?:竞赛|大纲)|(?:当前|目前).{0,20}(?:进展|版本|状态)|现在.*(?:解决|证明)|latest|recent\s+(?:research|paper)|news", text)
    claim = re.search(r"openai|deepmind|anthropic|谷歌|google|陶哲轩|某公司|某团队", text) and re.search(
        r"证明|解决|突破|获奖|发布|proved|solved|breakthrough", text)
    problem_status = re.search(
        r"(?:猜想|千禧问题|navier[\s–—-]*sto\w*|ns问题|纳维).{0,20}(?:被.*(?:证伪|证明)|证伪|解决|攻克|(?:证明|成立)(?:了|吗|嘛))", text)
    # Student attempts retain their diagnostic route even when mentioning news.
    attempt = re.search(r"我(?:的证明|证明如下|算|推导)|检查.*(?:步骤|证明)|哪里错|对吗|正确吗", text)
    return bool((news or claim or problem_status) and not attempt)


def decide_search(message: str, mode: str = "auto", legacy_enabled: bool = False) -> SearchDecision:
    factual = is_external_fact_question(message)
    if mode == "off":
        return SearchDecision(False, "explicit_off", factual)
    if mode == "on" or legacy_enabled:
        return SearchDecision(True, "explicit_on", factual)
    requested = bool(re.search(r"联网|搜索|查一下|查一查|核实|(?:^|[，。！？\s])查证|search\s+(?:the\s+)?web|look\s+up", message.lower()))
    return SearchDecision(factual or requested, "freshness" if factual else "requested" if requested else "not_needed", factual)


def search_query(message: str) -> str:
    # Common spelling/voice-input errors should not become retrieval anchors.
    query = re.sub(r"navier[\s–—-]*sto(?:rke|kes?)(?![a-z])", "Navier–Stokes", message, flags=re.I)
    if "openai" in query.lower() and "navier" in query.lower():
        return "OpenAI Navier Stokes proof"
    return query.strip()[:400]
