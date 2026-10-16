import logging
import re
from typing import Any, Optional

from app.knowledge.case_schema import CaseDecision, CaseMatchResult
from app.knowledge.course_service import get_course_service
from app.knowledge.schema import EvidencePack, KnowledgeHit, KnowledgeItem

logger = logging.getLogger(__name__)

# Positional relevance for course-graph hits, on a 0..1 scale. Only the
# ordering matters: the fusion layer in fast_context re-ranks by RRF, so these
# values are never compared against raw BM25/vector scores.
_ANCHOR_RELEVANCE = 1.0
_NEIGHBOUR_RELEVANCE = 0.6
# A subgraph can be returned without a matched case; assume middling confidence
# rather than treating the hits as certain.
_NO_CASE_CONFIDENCE = 0.5


class CourseEvidenceBuilder:
    """Builds an enriched, boundary-aware EvidencePack linking student query to Teaching Cases and graph anchors."""

    def __init__(self, course_id: str = "numerical_analysis"):
        self.course_id = course_id
        self.service = get_course_service(course_id)

    def _condition_details(self, case, allow_extension: bool) -> list[dict[str, Any]]:
        if not case:
            return []
        details = []
        for ref in case.required_condition_ids:
            unit = self.service.graph_repo.get_unit(ref)
            if unit:
                if unit.review_status == "verified" and self.service.graph_repo.boundary_checker.filter_units([ref], allow_extension=allow_extension):
                    details.append({"id": ref, "title": unit.title, "content": unit.content,
                                    "kind": "course_unit", "review_status": "verified", "verification_status": "not_checked"})
            elif not re.match(r"^(NA|MATH|OPT)_", ref):
                # Frozen v1 includes declarative conditions in this *_ids field.
                # They are metadata, not resolved nodes or established facts.
                details.append({"id": ref, "title": ref, "content": ref,
                                "kind": "case_declared_condition", "source_case_id": case.case_id,
                                "review_status": case.review_status, "verification_status": "not_checked"})
        return details

    def build_evidence_pack(
        self,
        query: str,
        student_id: Optional[str] = None,
        task_mode: Optional[str] = None,
        allow_extension: bool = False
    ) -> EvidencePack:
        # 1. Match Teaching Case
        match_result: CaseMatchResult = self.service.case_matcher.match(
            query=query,
            course_id=self.course_id,
            context={"task_mode": task_mode, "allow_extension": allow_extension}
        )

        matched_case = match_result.matched_case
        recalled_units = match_result.unit_candidates
        requested_anchors = list(dict.fromkeys(list(match_result.concept_anchor_ids) + [r["unit_id"] for r in recalled_units[:3]]))
        boundary_decision = self.service.graph_repo.boundary_checker.inspect_boundary_decision(
            requested_anchors, allow_extension=allow_extension)
        concept_anchors = self.service.graph_repo.boundary_checker.filter_units(requested_anchors, allow_extension=allow_extension)
        concept_anchors = [uid for uid in concept_anchors if (u := self.service.graph_repo.get_unit(uid)) and u.review_status == "verified"]
        effective_task = task_mode if task_mode in {"concept_explanation", "convergence_analysis", "derivation", "error_debugging", "code_task"} else (matched_case.task_type if matched_case else None)

        # 2. Extract Subgraph & Boundary Decision
        subgraph_units = []
        if concept_anchors:
            subgraph_units, _ = self.service.graph_repo.get_subgraph(
                center_unit_ids=concept_anchors,
                max_depth=1,
                task_mode=effective_task,
                allow_extension=allow_extension
            )

        allowed_units = set(self.service.graph_repo.boundary_checker.filter_units([u.id for u in subgraph_units], allow_extension=allow_extension))
        subgraph_units = [u for u in subgraph_units if u.id in allowed_units and u.review_status == "verified"]

        # 3. Pull Student History Refs (evidence counts only; mastery belongs to BKT)
        student_history_refs = []
        if student_id:
            overlay = self.service.overlay_store.get_course_overlay(student_id, self.course_id)
            for cid in concept_anchors:
                if cid in overlay.get("units", {}):
                    u_state = overlay["units"][cid]
                    student_history_refs.append({
                        "unit_id": cid,
                        "independent_evidence_count": u_state.get("independent_evidence_count", 0),
                        "assisted_success_count": u_state.get("assisted_success_count", 0),
                        "failure_count": u_state.get("failure_count", 0),
                        "hint_exposure_count": u_state.get("hint_exposure_count", 0),
                        "latest_outcome": u_state.get("latest_outcome", "unseen"),
                        "errors": u_state.get("misconception_candidate_refs", []),
                    })

        # 4. Construct Teaching Hints
        teaching_hints = []
        if match_result.clarification_question:
            teaching_hints.append({"type": "clarification", "question": match_result.clarification_question})
        if matched_case:
            for action in matched_case.possible_actions:
                teaching_hints.append(action)
            if matched_case.diagnostic_probes:
                teaching_hints.append({
                    "type": "diagnostic_probe",
                    "probe": matched_case.diagnostic_probes[0]
                })

        # 5. Assemble Graph Hits
        # Relevance is positional: a unit the case matcher anchored on is more
        # relevant than a 1-hop neighbour pulled in by subgraph expansion. The
        # previous constant score made every hit tie, so `hits[:3]` downstream
        # was simply the first three nodes in subgraph traversal order — the
        # injected knowledge had nothing to do with what the student asked.
        anchor_ids = set(concept_anchors)
        case_confidence = match_result.confidence if matched_case else _NO_CASE_CONFIDENCE
        graph_hits = []
        for u in subgraph_units:
            # Wrap as compatible KnowledgeHit
            k_item = KnowledgeItem(
                id=u.id,
                subject=self.course_id,
                source_file="course_pack",
                concept_zh=u.title,
                prerequisite=[
                    ref.get("display_name", "")
                    for ref in u.expected_prerequisites
                    if ref.get("display_name")
                ],
                description=u.content,
                intuitive_explanation=u.intuitive_explanation,
                solution=u.solution,
                type=u.type,
                difficulty=u.difficulty,
                # Attribution for the prompt: a bare fragment of a theorem is
                # much less usable than one that says which section it is from.
                chapter=u.chapter_path[0] if u.chapter_path else "",
                section=" › ".join(u.chapter_path[1:]) if len(u.chapter_path) > 1 else "",
            )
            relevance = _ANCHOR_RELEVANCE if u.id in anchor_ids else _NEIGHBOUR_RELEVANCE
            graph_hits.append(
                KnowledgeHit(item=k_item, score=int(relevance * case_confidence * 100))
            )
        graph_hits.sort(key=lambda hit: (hit.score, hit.item.concept_zh), reverse=True)

        return EvidencePack(
            retrieval_trace={"case_candidates": match_result.candidate_cases, "unit_candidates": recalled_units,
                             "reason": match_result.reason, "clarification_question": match_result.clarification_question,
                             "graph_generation": (saved["generation"] if (saved := self.service.store.load_graph(self.course_id)) else None),
                             "ranking_version": "course-bm25-v1", "confidence_kind": "heuristic_not_probability"},
            match_decision=match_result.decision.value,
            condition_details=self._condition_details(matched_case, allow_extension),
            citations=[
                {"id": u.id, "title": u.title,
                 "source": {"kind": "course_unit", "document_id": u.source_document_id,
                            "chapter": u.chapter_path, "page_start": u.page_start,
                            "page_end": u.page_end, "provenance": u.provenance}}
                for u in subgraph_units if u.review_status == "verified"
            ],
            query_scope={"course_id": self.course_id, "course_version": self.service.graph_repo.course_version, "task_mode": effective_task or "general"},
            direct_hits=[],
            graph_hits=graph_hits,
            confidence=match_result.confidence,
            teaching_hints=teaching_hints,
            matched_case=matched_case.to_dict() if matched_case else None,
            concept_anchors=concept_anchors,
            required_conditions=matched_case.required_condition_ids if matched_case else [],
            boundary_decision=boundary_decision,
            student_history_refs=student_history_refs,
        )
