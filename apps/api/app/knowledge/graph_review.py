import datetime
import logging
from typing import Any, Optional

from app.knowledge.candidate_graph import (
    CandidateManager,
    CandidateStatus,
    CandidateType,
    GraphCandidate,
)
from app.knowledge.course_store import CourseStore
from app.knowledge.graph_repository import CourseGraphRepository
from app.knowledge.schema import KnowledgeRelation, KnowledgeUnit
from app.knowledge.case_schema import TeachingCase
from app.knowledge.boundary import BoundaryPolicy, ScopeLevel

logger = logging.getLogger(__name__)


class GraphReviewService:
    """Manages the teacher review cycle for dynamic candidate evolution.

    Every approve/merge produces an immutable graph revision record so the
    canonical graph can be audited, rolled back, and pinned in benchmarks.
    """

    def __init__(
        self,
        graph_repo: CourseGraphRepository,
        candidate_mgr: CandidateManager,
        store: Optional[CourseStore] = None,
    ):
        self.graph_repo = graph_repo
        self.candidate_mgr = candidate_mgr
        self.store = store

    def _record_revision(
        self,
        candidate: GraphCandidate,
        action: str,
        applied_changes: dict[str, Any],
        reviewer_id: str,
        review_note: str,
    ) -> Optional[str]:
        if not self.store:
            return None
        revision_id = f"rev_{candidate.course_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        parent = self.store.latest_revision_id(candidate.course_id)
        self.store.append_revision(
            revision_id=revision_id,
            parent_revision_id=parent,
            course_id=candidate.course_id,
            candidate_id=candidate.candidate_id,
            action=action,
            changed_entities=applied_changes,
            reviewer_id=reviewer_id,
            reason=review_note,
        )
        return revision_id

    def review_candidate(
        self,
        candidate_id: str,
        action: str,  # "approve" | "merge" | "reject" | "defer"
        reviewer_id: str = "teacher",
        review_note: str = "",
        merge_target_id: Optional[str] = None
    ) -> dict[str, Any]:
        candidate = self.candidate_mgr.get_candidate(candidate_id)
        if not candidate:
            raise KeyError(f"Candidate {candidate_id} not found")

        # Update candidate status
        updated_candidate = self.candidate_mgr.review_candidate(
            candidate_id=candidate_id,
            action=action,
            reviewer_id=reviewer_id,
            review_note=review_note,
        )

        applied_changes: dict[str, Any] = {"candidate_id": candidate_id, "action": action}

        if action == "approve":
            c_type = candidate.candidate_type
            payload = candidate.payload

            if c_type == CandidateType.NEW_UNIT.value:
                unit = KnowledgeUnit(
                    id=payload.get("id", candidate_id),
                    course_id=candidate.course_id,
                    title=payload.get("title", ""),
                    type=payload.get("type", "concept"),
                    content=payload.get("content", ""),
                    latex=payload.get("latex", ""),
                    intuitive_explanation=payload.get("intuitive_explanation", ""),
                    solution=payload.get("solution", ""),
                    keywords=payload.get("keywords", []),
                    aliases=payload.get("aliases", []),
                    difficulty=int(payload.get("difficulty", 3)),
                    teaching_role=payload.get("teaching_role", "core"),
                    provenance=f"candidate_{candidate.proposed_by}",
                    review_status="verified",
                )
                scope = payload.get("scope_level", ScopeLevel.CORE.value)
                boundary = BoundaryPolicy(
                    course_id=candidate.course_id,
                    unit_id=unit.id,
                    scope_level=scope,
                    teacher_note=review_note,
                )
                self.graph_repo.add_unit(unit, boundary=boundary)
                applied_changes["entity_type"] = "unit"
                applied_changes["entity_id"] = unit.id

            elif c_type == CandidateType.NEW_RELATION.value:
                rel = KnowledgeRelation(
                    source_unit_id=payload["source_unit_id"],
                    target_unit_id=payload["target_unit_id"],
                    relation_type=payload["relation_type"],
                    confidence=float(payload.get("confidence", 1.0)),
                    provenance=f"candidate_{candidate.proposed_by}",
                    review_status="verified",
                )
                self.graph_repo.add_relation(rel)
                applied_changes["entity_type"] = "relation"
                applied_changes["relation"] = f"{rel.source_unit_id}->{rel.target_unit_id}"

            elif c_type == CandidateType.NEW_CASE.value:
                case = TeachingCase.from_dict(payload)
                case.review_status = "verified"
                case.provenance = f"candidate_{candidate.proposed_by}"
                self.graph_repo.add_case(case)
                applied_changes["entity_type"] = "case"
                applied_changes["entity_id"] = case.case_id

        elif action == "merge":
            target_id = merge_target_id or candidate.payload.get("target_id")
            if not target_id:
                raise ValueError("merge_target_id required for merge action")

            target_unit = self.graph_repo.get_unit(target_id)
            if target_unit:
                alias = candidate.payload.get("alias") or candidate.payload.get("title")
                if alias and alias not in target_unit.aliases:
                    target_unit.aliases.append(alias)
                    applied_changes["merged_into_unit"] = target_id
                    applied_changes["added_alias"] = alias
            else:
                target_case = self.graph_repo.case_repo.get_case(target_id)
                if target_case:
                    variant = candidate.payload.get("variant") or candidate.payload.get("title")
                    if variant and variant not in target_case.accepted_variants:
                        target_case.accepted_variants.append(variant)
                        applied_changes["merged_into_case"] = target_id
                        applied_changes["added_variant"] = variant

        return {
            "status": "success",
            "candidate": updated_candidate.to_dict(),
            "applied_changes": applied_changes,
            "revision_id": self._record_revision(candidate, action, applied_changes, reviewer_id, review_note),
        }
