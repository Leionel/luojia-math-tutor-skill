import re
from typing import Any, Optional

from app.knowledge.case_schema import (
    CaseDecision,
    CaseMatchResult,
    TeachingCase,
)
from app.knowledge.case_repository import TeachingCaseRepository


def _tokenize(text: str) -> set[str]:
    """Tokenize query into English terms and Chinese words/substrings."""
    text = text.lower().strip()
    words = set(re.findall(r"[a-z0-9_]+", text))
    # Add Chinese 2-4 gram segments
    cn_chars = re.findall(r"[\u4e00-\u9fff]", text)
    cn_text = "".join(cn_chars)
    for n in (2, 3, 4):
        for i in range(len(cn_text) - n + 1):
            words.add(cn_text[i : i + n])
    # Also add single characters for key terms
    for ch in cn_chars:
        words.add(ch)
    return words


class TeachingCaseMatcher:
    """Matches a student query or attempt to canonical Teaching Cases via multi-tier decision."""

    def __init__(self, repository: TeachingCaseRepository):
        self.repository = repository

    def match(
        self,
        query: str,
        course_id: str = "numerical_analysis",
        context: Optional[dict[str, Any]] = None
    ) -> CaseMatchResult:
        context = context or {}
        cases = self.repository.list_cases(course_id=course_id)
        if not cases:
            return CaseMatchResult(
                decision=CaseDecision.NEW_CASE,
                confidence=0.0,
                review_required=True,
            )

        query_tokens = _tokenize(query)

        # Layer 1: Candidate Recall & Scoring
        scored_candidates: list[tuple[TeachingCase, float, list[str]]] = []
        for case in cases:
            score = 0.0
            matched_aspects = []

            # Check exact variant match
            for var in case.accepted_variants:
                var_tokens = _tokenize(var)
                if not var_tokens:
                    continue
                overlap = len(query_tokens & var_tokens) / len(var_tokens)
                if overlap > 0.65:
                    score = max(score, 0.75 + 0.25 * overlap)
                    matched_aspects.append(f"variant_match: {var}")

            # Check title overlap
            title_tokens = _tokenize(case.title)
            if title_tokens:
                title_overlap = len(query_tokens & title_tokens) / len(title_tokens)
                if title_overlap > 0.4:
                    score = max(score, 0.5 + 0.4 * title_overlap)
                    matched_aspects.append(f"title_match: {case.title}")

            # Check objectives overlap
            obj_score = 0.0
            for obj in case.learning_objectives:
                obj_tokens = _tokenize(obj)
                if obj_tokens:
                    ol = len(query_tokens & obj_tokens) / len(obj_tokens)
                    obj_score = max(obj_score, ol)
            if obj_score > 0.35:
                score = max(score, 0.4 + 0.35 * obj_score)
                matched_aspects.append("objective_match")

            # Check concept anchors
            concept_overlap_count = 0
            for cid in case.concept_ids:
                c_tokens = _tokenize(cid.replace("_", " "))
                if query_tokens & c_tokens:
                    concept_overlap_count += 1
            if concept_overlap_count > 0:
                score += min(0.25, 0.08 * concept_overlap_count)

            if score > 0.2:
                scored_candidates.append((case, min(1.0, score), matched_aspects))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        # Build candidate summaries
        top_candidates = [
            {
                "case_id": c.case_id,
                "title": c.title,
                "task_type": c.task_type,
                "score": round(score, 4),
                "matched_aspects": aspects,
                "concept_ids": c.concept_ids,
            }
            for c, score, aspects in scored_candidates[:5]
        ]

        if not scored_candidates or scored_candidates[0][1] < 0.35:
            return CaseMatchResult(
                decision=CaseDecision.NEW_CASE,
                confidence=round(scored_candidates[0][1] if scored_candidates else 0.0, 4),
                candidate_cases=top_candidates,
                review_required=True,
            )

        best_case, best_score, best_aspects = scored_candidates[0]

        # Layer 2: Structural feature & difference axis analysis
        difference_axes = []
        task_mode = context.get("task_mode")
        if task_mode and task_mode != best_case.task_type:
            difference_axes.append("task_type")

        # Check condition-specific keywords (e.g. multiple root vs simple root, local vs global)
        if "重根" in query or "multiple" in query.lower():
            if "MATH_MULTIPLE_ROOT" not in best_case.concept_ids and "multiple_root" not in best_case.case_id.lower():
                difference_axes.append("multiple_root_condition")
        if "初值" in query or "initial" in query.lower():
            if "initial" not in best_case.case_id.lower() and "initial_guess" not in "".join(best_case.required_condition_ids).lower():
                difference_axes.append("initial_value_condition")
        if "残差" in query or "residual" in query.lower():
            if "residual" not in best_case.case_id.lower() and "NA_RESIDUAL" not in best_case.concept_ids:
                difference_axes.append("residual_vs_error")

        # Layer 3: Decision classification
        diagnostic_probe = best_case.diagnostic_probes[0] if best_case.diagnostic_probes else None

        if best_score >= 0.85 and not difference_axes:
            decision = CaseDecision.SAME_CASE
            review_required = False
        elif best_score >= 0.55:
            if difference_axes:
                decision = CaseDecision.VARIANT_OF_CASE
                review_required = False
            else:
                decision = CaseDecision.SAME_CASE
                review_required = False
        elif best_score >= 0.40:
            decision = CaseDecision.RELATED_CASE
            review_required = False
        else:
            decision = CaseDecision.UNCERTAIN
            review_required = True

        return CaseMatchResult(
            decision=decision,
            matched_case_id=best_case.case_id,
            matched_case=best_case,
            confidence=round(best_score, 4),
            candidate_cases=top_candidates,
            concept_anchor_ids=best_case.concept_ids,
            difference_axes=difference_axes,
            diagnostic_probe=diagnostic_probe,
            review_required=review_required,
        )
