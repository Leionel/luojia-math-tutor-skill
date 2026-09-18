import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from app.knowledge.course_store import CourseStore


class CandidateType(str, Enum):
    NEW_UNIT = "new_unit"
    NEW_RELATION = "new_relation"
    MERGE_UNITS = "merge_units"
    NEW_CASE = "new_case"
    NEW_ALIAS = "new_alias"
    SCOPE_CHANGE = "scope_change"


class CandidateStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    MERGED = "merged"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass
class GraphCandidate:
    candidate_id: str
    candidate_type: str
    course_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    proposed_by: str = "system"  # teacher | system | student_query_cluster
    support_count: int = 1
    status: str = CandidateStatus.PENDING.value
    reviewer_id: Optional[str] = None
    review_note: str = ""
    first_seen: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "course_id": self.course_id,
            "payload": self.payload,
            "evidence_refs": self.evidence_refs,
            "proposed_by": self.proposed_by,
            "support_count": self.support_count,
            "status": self.status,
            "reviewer_id": self.reviewer_id,
            "review_note": self.review_note,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphCandidate":
        return cls(
            candidate_id=data["candidate_id"],
            candidate_type=data.get("candidate_type", CandidateType.NEW_UNIT.value),
            course_id=data.get("course_id", "numerical_analysis"),
            payload=data.get("payload", {}),
            evidence_refs=data.get("evidence_refs", []),
            proposed_by=data.get("proposed_by", "system"),
            support_count=data.get("support_count", 1),
            status=data.get("status", CandidateStatus.PENDING.value),
            reviewer_id=data.get("reviewer_id"),
            review_note=data.get("review_note", ""),
            first_seen=data.get("first_seen", datetime.datetime.now().isoformat()),
            last_seen=data.get("last_seen", datetime.datetime.now().isoformat()),
        )


class CandidateManager:
    """Manages the evolution candidate buffer to ensure no unreviewed updates pollute the canonical graph.

    When a CourseStore is provided, candidates are loaded from it on startup and
    every add/review is written through, so state survives server restarts.
    """

    def __init__(self, candidates: Optional[list[GraphCandidate]] = None, store: Optional[CourseStore] = None):
        self.store = store
        self._candidates: dict[str, GraphCandidate] = {
            c.candidate_id: c for c in (candidates or [])
        }
        if store:
            for d in store.load_candidates():
                if d.get("candidate_id") not in self._candidates:
                    c = GraphCandidate.from_dict(d)
                    self._candidates[c.candidate_id] = c

    def _persist(self, candidate: GraphCandidate) -> None:
        if self.store:
            self.store.upsert_candidate(candidate.candidate_id, candidate.course_id, candidate.to_dict())

    def add_candidate(
        self,
        candidate_id: str,
        candidate_type: str,
        course_id: str,
        payload: dict[str, Any],
        proposed_by: str = "system",
        evidence_ref: Optional[str] = None
    ) -> GraphCandidate:
        now = datetime.datetime.now().isoformat()
        if candidate_id in self._candidates:
            existing = self._candidates[candidate_id]
            existing.support_count += 1
            existing.last_seen = now
            if evidence_ref and evidence_ref not in existing.evidence_refs:
                existing.evidence_refs.append(evidence_ref)
            self._persist(existing)
            return existing

        c = GraphCandidate(
            candidate_id=candidate_id,
            candidate_type=candidate_type,
            course_id=course_id,
            payload=payload,
            evidence_refs=[evidence_ref] if evidence_ref else [],
            proposed_by=proposed_by,
            support_count=1,
            status=CandidateStatus.PENDING.value,
            first_seen=now,
            last_seen=now
        )
        self._candidates[candidate_id] = c
        self._persist(c)
        return c

    def get_candidate(self, candidate_id: str) -> Optional[GraphCandidate]:
        return self._candidates.get(candidate_id)

    def list_candidates(
        self,
        course_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> list[GraphCandidate]:
        results = list(self._candidates.values())
        if course_id:
            results = [c for c in results if c.course_id == course_id]
        if status:
            results = [c for c in results if c.status == status]
        return results

    def review_candidate(
        self,
        candidate_id: str,
        action: str,  # "approve" | "merge" | "reject" | "defer"
        reviewer_id: str = "teacher",
        review_note: str = ""
    ) -> GraphCandidate:
        candidate = self._candidates.get(candidate_id)
        if not candidate:
            raise KeyError(f"Candidate {candidate_id} not found")

        action_map = {
            "approve": CandidateStatus.APPROVED.value,
            "merge": CandidateStatus.MERGED.value,
            "reject": CandidateStatus.REJECTED.value,
            "defer": CandidateStatus.DEFERRED.value,
        }
        if action not in action_map:
            raise ValueError(f"Invalid review action: {action}")

        candidate.status = action_map[action]
        candidate.reviewer_id = reviewer_id
        candidate.review_note = review_note
        candidate.last_seen = datetime.datetime.now().isoformat()
        self._persist(candidate)
        return candidate
