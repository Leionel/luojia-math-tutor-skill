from typing import Any, Optional
from app.knowledge.case_schema import CaseDecision, CaseMatchResult, TaskType
from app.knowledge.case_repository import TeachingCaseRepository
from app.knowledge.course_retrieval import ALGORITHMS, FEATURES, OUTSIDE, UNSUPPORTED, features, normalize, rank_documents
import re


class TeachingCaseMatcher:
    """BM25 metadata recall followed by course/task/condition decisions.

    confidence is a deterministic ranking heuristic, not a calibrated probability
    and never a verifier outcome. Candidate recall is retained when abstaining.
    """
    def __init__(self, repository: TeachingCaseRepository, graph_repo=None):
        self.repository, self.graph_repo = repository, graph_repo

    def match(self, query: str, course_id: str = "numerical_analysis", context: Optional[dict[str, Any]] = None) -> CaseMatchResult:
        result = self._match(query, course_id, context)
        if self.graph_repo and self.graph_repo.course_id == course_id and result.reason not in ("out_of_course", "missing_task_anchor"):
            result.unit_candidates = self.graph_repo.search_units(query, allow_extension=bool((context or {}).get("allow_extension", False)))
        return result

    def _match(self, query: str, course_id: str = "numerical_analysis", context: Optional[dict[str, Any]] = None) -> CaseMatchResult:
        context = context or {}
        task_mode = context.get("task_mode")
        if task_mode not in {t.value for t in TaskType}:
            task_mode = None
        extra = " ".join(context.get(k, "") for k in ("problem", "attempt", "code", "task_context") if isinstance(context.get(k), str))
        text = query + " " + extra
        qf = features(text)
        if "bracket" in qf and not (qf & ALGORITHMS) and not (qf & {"contraction", "residual"}):
            qf.add("bisection")
        if "multiple" in qf and not (qf & ALGORITHMS):
            qf.add("newton")
        cases = [c for c in self.repository.list_cases(course_id=course_id) if c.review_status == "verified"]
        # Unknown course IDs must not fall back to another course's ontology.
        if not cases:
            return CaseMatchResult(CaseDecision.NEW_CASE, review_required=True, reason="no_verified_cases")
        domain = " ".join(c.title + " " + " ".join(c.accepted_variants) for c in cases)
        for pattern, reason in ((OUTSIDE, "out_of_course"), (UNSUPPORTED, "absent_from_case_ontology")):
            hit = re.search(pattern, text, re.I)
            comparison = pattern == UNSUPPORTED and bool(qf & ALGORITHMS) and bool(re.search(r"区别|差别|比较|compare|difference", text, re.I))
            if hit and not comparison and not re.search(re.escape(hit.group()), domain, re.I):
                return CaseMatchResult(CaseDecision.NEW_CASE, review_required=True, reason=reason)
        docs, profiles = [], {}
        for c in cases:
            description = " ".join([c.title] * 3 + c.accepted_variants * 2 + c.learning_objectives)
            profiles[c.case_id] = features(description)
            anchors = []
            if self.graph_repo:
                anchors = [u.title + " " + " ".join(u.aliases + u.keywords) for uid in c.concept_ids
                           if (u := self.graph_repo.get_unit(uid)) and u.review_status == "verified"]
            docs.append({"id": c.case_id, "text": normalize(description + " " + " ".join(anchors))})
        lexical = dict(rank_documents(text, docs))
        max_lex = max(lexical.values(), default=1)
        scored = []
        qalg = qf & ALGORITHMS
        code = task_mode == "code_task" or "code" in qf
        for c in cases:
            cf = profiles[c.case_id]
            bm25 = lexical.get(c.case_id, 0)
            score = 0.35 * bm25 / max_lex
            reasons = [f"bm25:{bm25:.4f}"]
            if qalg:
                same = bool(qalg & cf)
                score += 0.28 if same else (-0.6 if cf & ALGORITHMS else 0)
                reasons.append("algorithm_agreement" if same else "algorithm_conflict")
            # Sparse structural facets disambiguate Cases sharing an algorithm.
            common = (qf & cf) - ALGORITHMS - {"code", "error", "derivative", "numeric"}
            score += min(0.32, 0.08 * len(common))
            focus = features(c.title)
            if "local" in qf:
                score += 0.38 if "local" in focus else -0.1
            if "derive" in qf and not (qf & {"zero", "multiple", "local"}):
                score += 0.28 if c.task_type == "derivation" else -0.08
            if "stop" in qf and not ("residual" in qf and "error" in qf) and not ("numeric" in qf and "order" in qf):
                score += 0.4 if "stop" in focus else -0.12
            for tag in ("multiple", "initial", "residual", "rearrange", "derive", "contraction"):
                if tag in qf and tag in focus:
                    score += 0.18
            if "bisection" in qf:
                if "bound" in qf or ("error" in qf and "bracket" in qf):
                    score += 0.35 if "bound" in focus else -0.12
                elif "update" in qf or ("code" in qf and "condition" not in qf):
                    score += 0.35 if "update" in focus else -0.12
                elif "condition" in qf or "bracket" in qf:
                    score += 0.25 if "condition" in focus else -0.1
            if "fixed" in qf and ("condition" in qf or "contraction" in qf) and "rearrange" not in qf and "diverge" not in qf:
                score += 0.22 if "condition" in focus else -0.12
            if "fixed" in qf and ("diverge" in qf or "rearrange" in qf):
                score += 0.25 if "rearrange" in focus else -0.1
            if "multiple" in qf:
                score += 0.35 if "multiple" in cf else -0.25
            if "residual" in qf:
                score += 0.24 if "residual" in cf else -0.12
            if "zero" in qf and "derivative" in cf:
                score += 0.20 if "zero" in cf else 0
            if code:
                score += 0.28 if c.task_type == "code_task" else -0.13
                if "newton" in qf:
                    if qf & {"update", "derivative", "zero"}:
                        score += 0.3 if "update" in focus and c.task_type == "code_task" else 0
                    elif "stop" in qf:
                        score += 0.3 if "stop" in focus and "update" not in focus and c.task_type == "code_task" else 0
            elif c.task_type == "code_task" and "numeric" not in qf:
                score -= 0.16
            if "numeric" in qf and "order" in qf:
                score += 0.3 if "numeric" in cf and "order" in cf else -0.12
            if task_mode and task_mode == c.task_type:
                score += 0.08
            # Verbatim variants remain compatible with the original 20 cases.
            if any(v.lower() in text.lower() for v in c.accepted_variants if v):
                score += 0.4
                reasons.append("accepted_variant")
            reasons.extend(sorted(common))
            if bm25 > 0 or (qalg & cf):
                scored.append((c, score, reasons))
        scored.sort(key=lambda row: (-row[1], row[0].case_id))
        summaries = [{"case_id": c.case_id, "title": c.title, "task_type": c.task_type,
                      "score": round(s, 4), "matched_aspects": r, "concept_ids": c.concept_ids}
                     for c, s, r in scored[:5]]
        if not scored or scored[0][1] < 0.25:
            return CaseMatchResult(CaseDecision.NEW_CASE, candidate_cases=summaries, review_required=True, reason="low_course_relevance")
        best, score, _ = scored[0]
        gap = score - scored[1][1] if len(scored) > 1 else score
        # An unqualified query must not receive an invented algorithm/Case.
        if re.search(r"只说.*作业|不确定.*(二分|Newton|牛顿)|某个.*算法|某算法|some.*algorithm", text, re.I) or (not qalg and not (qf & {"residual", "stop", "multiple", "contraction", "derivative", "bound", "order", "derive", "local"}) and score < 0.65):
            return CaseMatchResult(CaseDecision.UNCERTAIN, candidate_cases=summaries, review_required=True,
                                   clarification_question="请补充使用的算法、函数或迭代步骤。", reason="missing_task_anchor")
        if gap < 0.012 and score < 0.6:
            return CaseMatchResult(CaseDecision.UNCERTAIN, candidate_cases=summaries, review_required=True,
                                   clarification_question="你要检查使用条件、更新步骤，还是停止准则？", reason="ambiguous_candidates")
        axes = []
        if task_mode and task_mode != best.task_type:
            axes.append("task_type")
        for key in ("multiple", "residual"):
            if key in qf and key not in profiles[best.case_id]:
                axes.append(f"{key}_condition")
        decision = CaseDecision.VARIANT_OF_CASE if axes else CaseDecision.SAME_CASE
        clarification = None
        if re.search(r"没.*(提供|给|算)|没有|未知|previous.*run|earlier chat|does not converge", text, re.I):
            clarification = "请提供函数、使用条件、初值和出现问题的迭代步骤；当前匹配只确定教学主题，尚不能定位错误。"
        return CaseMatchResult(decision, matched_case_id=best.case_id, matched_case=best,
                               confidence=round(min(1, max(0, score)), 4), candidate_cases=summaries,
                               concept_anchor_ids=best.concept_ids, difference_axes=axes,
                               diagnostic_probe=best.diagnostic_probes[0] if best.diagnostic_probes else None,
                               clarification_question=clarification, reason="metadata_and_task_match")
