"""Goal-directed targeted retrieval for pedagogical decisions (R3.3).

Instead of flooding every turn with wide context, targeted retrieval only
fires when a specific gap is detected:
1. theorem_conditions: when missing conditions need theorem premises.
2. counterexample: when overgeneralization requires an illustrative counterexample.
3. prerequisite: when foundational definition or concept explanation is needed.
4. worked_step: when standard derivation or illustrative step is requested.

Strict invariants:
- At most 1 targeted search per turn.
- At most 3 evidence snippets.
- Results provide provenance and scope; finding a condition does NOT mean
  the student has satisfied it.
"""
from dataclasses import dataclass
from typing import Literal
import hashlib
import re
from app.knowledge.course_retrieval import ALGORITHMS, OUTSIDE, UNSUPPORTED, features


TargetGoal = Literal["theorem_conditions", "counterexample", "prerequisite", "worked_step"]

TARGET_EXPANSIONS: dict[TargetGoal, str] = {
    "theorem_conditions": "前提 条件 假设 连续 可导 导数非零 李普希兹 Lipschitz 局部收敛定理 单调性 充分条件",
    "counterexample": "反例 发散 振荡 周期循环 鞍点 重根 导数近零 割线 失败 极值点 假收敛",
    "prerequisite": "先修 定义 概念 含义 误差定义 残差 不动点 收敛阶 渐近误差",
    "worked_step": "例题 推导 步骤 算法计算 泰勒展开 格式迭代 规范步骤",
}


@dataclass(frozen=True)
class TargetedEvidenceSnippet:
    id: str
    goal: TargetGoal
    title: str
    content: str
    chapter_path: str | None
    review_status: str
    provenance: str
    scope: str = "reference_provenance_only"
    content_hash: str = ""
    graph_revision: str = ""


@dataclass
class TargetedRetrievalResult:
    goal: TargetGoal
    snippets: list[TargetedEvidenceSnippet]
    status: Literal["hit", "low_recall", "empty"]
    total_recalled: int
    provenance_version: str = "v1"


def infer_target_goal(decision_action: str | None, missing_conditions: list[str] | None = None, claim_status: str | None = None) -> TargetGoal | None:
    """Infer the targeted retrieval goal from the pedagogical gap."""
    if decision_action == "ask_missing_condition" or (missing_conditions and len(missing_conditions) > 0):
        return "theorem_conditions"
    if decision_action in {"correct_claim", "offer_experiment"} or claim_status == "contradicted":
        return "counterexample"
    if decision_action == "explain" or claim_status == "unknown":
        return "prerequisite"
    if decision_action == "offer_probe":
        return "worked_step"
    return None


class TargetedCourseRetriever:
    """Retrieves up to 3 bounded evidence snippets specifically serving a target goal."""

    def __init__(self, course_service=None):
        self.course_service = course_service

    def retrieve(self, query: str, goal: TargetGoal, max_snippets: int = 3) -> TargetedRetrievalResult:
        if goal not in TARGET_EXPANSIONS or type(max_snippets) is not int or max_snippets < 1:
            raise ValueError("Invalid targeted retrieval goal or budget")
        max_snippets = min(max_snippets, 3)
        if (not query.strip() or re.search(f"{OUTSIDE}|{UNSUPPORTED}", query, re.I)
                or not (features(query) & ALGORITHMS or re.search(r"求根|非线性方程", query))):
            return TargetedRetrievalResult(goal=goal, snippets=[], status="empty", total_recalled=0)
        # Keep the student's topic as the main query; broad vocabulary from every
        # algorithm would otherwise make unrelated units appear relevant.
        expansion = {"theorem_conditions": "前提 条件", "counterexample": "反例 发散",
                     "prerequisite": "定义 概念", "worked_step": "推导 步骤"}[goal]
        augmented_query = f"{query[:2000]} {expansion}"

        repo = getattr(self.course_service, "graph_repo", None)
        if repo is None:
            from app.knowledge.course_service import get_course_service
            self.course_service = get_course_service("numerical_analysis")
            repo = self.course_service.graph_repo

        # Production repository exposes search_units/get_unit, not get_all_units.
        # Its search enforces course boundaries and verified-only review status.
        ranked = repo.search_units(augmented_query, limit=max_snippets, allow_extension=False)
        store = self.course_service.store
        graph = store.load_graph(repo.course_id) or {}
        revision = store.latest_revision_id(repo.course_id) or f"seed:{graph.get('seed_checksum', '')}"

        snippets: list[TargetedEvidenceSnippet] = []
        for match in ranked:
            unit = repo.get_unit(match["unit_id"])
            if not unit or unit.review_status != "verified" or unit.course_id != repo.course_id:
                continue

            # Format concise excerpt
            content_excerpt = unit.content.strip()
            if len(content_excerpt) > 400:
                content_excerpt = content_excerpt[:400] + "…"

            snippets.append(TargetedEvidenceSnippet(
                id=f"targeted:{len(snippets)}",
                goal=goal,
                title=unit.title,
                content=content_excerpt,
                chapter_path="/".join(unit.chapter_path),
                review_status=unit.review_status,
                provenance=f"course_unit:{unit.id}",
                scope="reference_provenance_only",
                content_hash=hashlib.sha256(unit.content.encode()).hexdigest(),
                graph_revision=revision,
            ))
            if len(snippets) >= max_snippets:
                break

        status = "hit" if snippets else "empty"
        if snippets and len(snippets) < max_snippets:
            status = "low_recall"

        return TargetedRetrievalResult(
            goal=goal,
            snippets=snippets,
            status=status,
            total_recalled=len(ranked),
            provenance_version="v1",
        )
