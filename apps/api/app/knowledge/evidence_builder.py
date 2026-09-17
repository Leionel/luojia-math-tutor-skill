import logging
from typing import Any, Optional

from app.knowledge.case_schema import CaseDecision, CaseMatchResult
from app.knowledge.course_service import get_course_service
from app.knowledge.schema import EvidencePack, KnowledgeHit, KnowledgeItem

logger = logging.getLogger(__name__)


class CourseEvidenceBuilder:
    """Builds an enriched, boundary-aware EvidencePack linking student query to Teaching Cases and graph anchors."""

    def __init__(self, course_id: str = "numerical_analysis"):
        self.course_id = course_id
        self.service = get_course_service(course_id)

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
            context={"task_mode": task_mode}
        )

        matched_case = match_result.matched_case
        concept_anchors = list(match_result.concept_anchor_ids)

        # 2. Extract Subgraph & Boundary Decision
        subgraph_units = []
        if concept_anchors:
            subgraph_units, _ = self.service.graph_repo.get_subgraph(
                center_unit_ids=concept_anchors,
                max_depth=1,
                task_mode=task_mode,
                allow_extension=allow_extension
            )

        boundary_decision = self.service.graph_repo.boundary_checker.inspect_boundary_decision(
            target_unit_ids=concept_anchors,
            allow_extension=allow_extension
        )

        # 3. Pull Student History Refs
        student_history_refs = []
        if student_id:
            overlay = self.service.overlay_store.get_course_overlay(student_id, self.course_id)
            for cid in concept_anchors:
                if cid in overlay.get("units", {}):
                    u_state = overlay["units"][cid]
                    student_history_refs.append({
                        "unit_id": cid,
                        "mastery": u_state.get("mastery_estimate", 0.5),
                        "errors": u_state.get("misconception_candidate_refs", []),
                        "independent_count": u_state.get("independent_evidence_count", 0),
                    })

        # 4. Construct Teaching Hints
        teaching_hints = []
        if matched_case:
            for action in matched_case.possible_actions:
                teaching_hints.append(action)
            if matched_case.diagnostic_probes:
                teaching_hints.append({
                    "type": "diagnostic_probe",
                    "probe": matched_case.diagnostic_probes[0]
                })

        # 5. Assemble Graph Hits
        graph_hits = []
        for u in subgraph_units:
            # Wrap as compatible KnowledgeHit
            k_item = KnowledgeItem(
                id=u.id,
                subject=self.course_id,
                source_file="course_pack",
                concept_zh=u.title,
                prerequisite=[],
                description=u.content,
                intuitive_explanation=u.intuitive_explanation,
                solution=u.solution,
                type=u.type,
                difficulty=u.difficulty,
            )
            graph_hits.append(KnowledgeHit(item=k_item, score=85))

        return EvidencePack(
            query_scope={"course_id": self.course_id, "task_mode": task_mode or "general"},
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
