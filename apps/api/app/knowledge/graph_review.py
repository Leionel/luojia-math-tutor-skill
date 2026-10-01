import datetime
import threading
import uuid
from copy import deepcopy
from dataclasses import fields
from typing import Any, Optional
from pydantic import TypeAdapter

from app.knowledge.candidate_graph import CandidateManager, CandidateStatus, CandidateType, GraphCandidate
from app.knowledge.course_store import CourseStore
from app.knowledge.graph_repository import CourseGraphRepository, TASK_TYPE_RELATIONS
from app.knowledge.schema import KnowledgeRelation, KnowledgeUnit
from app.knowledge.case_schema import TeachingCase, TaskType, DisclosurePolicy
from app.knowledge.boundary import BoundaryPolicy, ScopeLevel


class GraphReviewService:
    """Validate on a private graph; publish only after the SQLite CAS commit."""

    def __init__(self, graph_repo: CourseGraphRepository, candidate_mgr: CandidateManager,
                 store: Optional[CourseStore] = None):
        self.graph_repo, self.candidate_mgr, self.store = graph_repo, candidate_mgr, store
        self._lock = store._lock if store else threading.RLock()
        self._receipts: dict[str, dict[str, Any]] = {}
        if store:
            saved = store.initialize_graph(graph_repo.course_id, graph_repo.to_course_pack(), "manual_initialization")
            graph_repo.replace_from_course_pack(saved["data"])

    def _apply(self, graph: CourseGraphRepository, c: GraphCandidate, action: str,
               target: Optional[str], note: str, reviewer: str) -> dict[str, Any]:
        p = deepcopy(c.payload)
        changes: dict[str, Any] = {"candidate_id": c.candidate_id, "action": action}
        if p.get("course_id", c.course_id) != c.course_id:
            raise ValueError("Payload course differs from candidate course")
        if action in ("reject", "defer"):
            return changes
        if action == "merge" or c.candidate_type == CandidateType.NEW_ALIAS.value:
            target = target or p.get("target_id")
            unit, case = graph.get_unit(target), graph.case_repo.get_case(target)
            if not unit and not case:
                raise ValueError("Merge target does not exist in this course")
            value = p.get("alias") or p.get("variant") or p.get("title")
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Non-empty alias/variant required")
            values = unit.aliases if unit else case.accepted_variants
            if value not in values:
                values.append(value)
            return {**changes, "merged_into_unit" if unit else "merged_into_case": target,
                    "added_alias" if unit else "added_variant": value}
        if c.candidate_type == CandidateType.NEW_UNIT.value:
            uid = p.get("id", c.candidate_id)
            if not isinstance(uid, str) or not uid.strip() or uid in graph.units:
                raise ValueError("Unit id is empty or already exists; use merge")
            if not isinstance(p.get("title"), str) or not p["title"].strip():
                raise ValueError("Unit title required")
            for key in ("keywords", "aliases", "chapter_path"):
                if not isinstance(p.get(key, []), list) or any(not isinstance(v, str) for v in p.get(key, [])):
                    raise ValueError(f"{key} must be a list of strings")
            difficulty = p.get("difficulty", 3)
            if not isinstance(difficulty, int) or isinstance(difficulty, bool) or not 1 <= difficulty <= 5:
                raise ValueError("difficulty must be an integer in 1..5")
            scope = ScopeLevel(p.get("scope_level", "core")).value
            kwargs = {f.name: p[f.name] for f in fields(KnowledgeUnit) if f.name in p}
            kwargs.update(id=uid, course_id=c.course_id, provenance=f"candidate_{c.proposed_by}",
                          review_status="verified", reviewer_id=reviewer)
            graph.add_unit(TypeAdapter(KnowledgeUnit).validate_python(kwargs), BoundaryPolicy(c.course_id, uid, scope_level=scope, teacher_note=note))
            return {**changes, "entity_type": "unit", "entity_id": uid}
        if c.candidate_type == CandidateType.NEW_RELATION.value:
            for key in ("source_unit_id", "target_unit_id", "relation_type"):
                if not isinstance(p.get(key), str) or not p[key].strip():
                    raise ValueError(f"{key} required")
            if any(graph.get_unit(p[key]) is None for key in ("source_unit_id", "target_unit_id")):
                raise ValueError("Relation endpoints must exist in this course")
            supported_relations = set().union(*TASK_TYPE_RELATIONS.values()) | {
                "prerequisite", "supports_proof", "derives", "applies_to", "algorithm_of", "code_task_of", "contrast_with"}
            if p["relation_type"] not in supported_relations:
                raise ValueError("Unknown relation type")
            confidence = float(p.get("confidence", 1))
            if not 0 <= confidence <= 1:
                raise ValueError("Invalid relation confidence")
            graph.add_relation(KnowledgeRelation(p["source_unit_id"], p["target_unit_id"], p["relation_type"],
                                                confidence, f"candidate_{c.proposed_by}", "verified"))
            return {**changes, "entity_type": "relation", "relation": f'{p["source_unit_id"]}->{p["target_unit_id"]}'}
        if c.candidate_type == CandidateType.NEW_CASE.value:
            if not isinstance(p.get("case_id"), str) or not p["case_id"] or graph.case_repo.get_case(p["case_id"]):
                raise ValueError("Case id required and must not already exist")
            if not isinstance(p.get("title"), str) or not p["title"].strip():
                raise ValueError("Case title required")
            TaskType(p.get("task_type", "concept_explanation"))
            DisclosurePolicy(p.get("disclosure_policy", "scaffolded"))
            for key in ("concept_ids", "required_condition_ids"):
                if not isinstance(p.get(key, []), list) or any(not isinstance(uid, str) or uid not in graph.units for uid in p.get(key, [])):
                    raise ValueError(f"{key} must reference existing course units")
            case = TypeAdapter(TeachingCase).validate_python(TeachingCase.from_dict({**p, "course_id": c.course_id}).to_dict())
            case.review_status, case.provenance = "verified", f"candidate_{c.proposed_by}"
            graph.add_case(case)
            return {**changes, "entity_type": "case", "entity_id": case.case_id}
        if c.candidate_type == CandidateType.SCOPE_CHANGE.value:
            uid = p.get("unit_id") or p.get("target_id")
            if uid not in graph.units:
                raise ValueError("Boundary target not found")
            scope = ScopeLevel(p.get("scope_level")).value
            policy = graph.boundary_checker.get_policy(uid) or BoundaryPolicy(c.course_id, uid)
            policy.scope_level, policy.teacher_note = scope, note
            graph.boundary_checker.set_policy(policy)
            return {**changes, "entity_type": "boundary", "entity_id": uid}
        raise ValueError(f"Unsupported approve type: {c.candidate_type}")

    def review_candidate(self, candidate_id: str, action: str, reviewer_id: str = "teacher",
                         review_note: str = "", merge_target_id: Optional[str] = None) -> dict[str, Any]:
        status_map = {"approve": "approved", "merge": "merged", "reject": "rejected", "defer": "deferred"}
        if action not in status_map:
            raise ValueError("Invalid review action")
        with self._lock:
            candidate = self.candidate_mgr.get_candidate(candidate_id)
            if self.store and self.store.persistent:
                saved_candidates = self.store.load_candidates(self.graph_repo.course_id)
                data = next((d for d in saved_candidates if d["candidate_id"] == candidate_id), None)
                candidate = GraphCandidate.from_dict(data) if data else None
            if not candidate or candidate.course_id != self.graph_repo.course_id:
                raise KeyError(candidate_id)
            request = {"action": action, "merge_target_id": merge_target_id}
            revisions = self.store.list_revisions(candidate.course_id) if self.store else []
            previous = next((r for r in reversed(revisions) if r["candidate_id"] == candidate_id), None)
            receipt = self._receipts.get(candidate_id)
            if previous and previous["changed_entities"].get("review_request") == request and candidate.status == status_map[action]:
                saved = self.store.load_graph(candidate.course_id)
                self.graph_repo.replace_from_course_pack(saved["data"])
                self.candidate_mgr._candidates[candidate_id] = candidate
                return {"status": "success", "duplicate": True, "candidate": candidate.to_dict(),
                        "revision_id": previous["revision_id"], "applied_changes": previous["changed_entities"]}
            if receipt and receipt["request"] == request and candidate.status == status_map[action]:
                return {**receipt["result"], "duplicate": True}
            if candidate.status not in (CandidateStatus.PENDING.value, CandidateStatus.DEFERRED.value):
                raise ValueError("Candidate already reviewed; conflicting request or legacy recovery required")
            saved = self.store.load_graph(candidate.course_id) if self.store else None
            before = saved["data"] if saved else self.graph_repo.to_course_pack()
            private = CourseGraphRepository(candidate.course_id)
            private.load_from_course_pack(deepcopy(before))
            try:
                changes = self._apply(private, candidate, action, merge_target_id, review_note, reviewer_id)
            except (TypeError, KeyError) as exc:
                raise ValueError(f"Invalid candidate payload: {exc}") from exc
            after = private.to_course_pack()
            updated = deepcopy(candidate)
            updated.status, updated.reviewer_id, updated.review_note = status_map[action], reviewer_id, review_note
            updated.last_seen = datetime.datetime.now(datetime.timezone.utc).isoformat()
            changes.update(review_request=request, before=before, after=after, evidence_refs=candidate.evidence_refs)
            revision = {"revision_id": f"rev_{uuid.uuid4().hex}", "parent_revision_id": self.store.latest_revision_id(candidate.course_id) if self.store else None,
                        "course_id": candidate.course_id, "candidate_id": candidate_id, "action": action,
                        "changed_entities": changes, "reviewer_id": reviewer_id, "reason": review_note,
                        "created_at": updated.last_seen}
            if self.store:
                self.store.commit_review(candidate.to_dict(), updated.to_dict(), after, saved["generation"], revision)
            self.graph_repo.replace_from_course_pack(after)
            self.candidate_mgr._candidates[candidate_id] = updated
            result = {"status": "success", "candidate": updated.to_dict(), "applied_changes": changes, "revision_id": revision["revision_id"]}
            self._receipts[candidate_id] = {"request": request, "result": result}
            return result
