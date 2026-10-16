import copy
import datetime
from dataclasses import dataclass, field
from typing import Any, Optional

from app.knowledge.course_store import CourseStore


@dataclass
class StudentUnitState:
    student_id: str
    course_id: str
    unit_id: str
    independent_evidence_count: int = 0
    assisted_success_count: int = 0
    attempt_count: int = 0
    failure_count: int = 0
    hint_exposure_count: int = 0
    latest_outcome: str = "unseen"  # unseen | success | assisted_success | failed
    recent_error_refs: list[str] = field(default_factory=list)
    misconception_candidate_refs: list[str] = field(default_factory=list)
    last_practiced_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_from_event_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "unit_id": self.unit_id,
            "mastery_estimate": None,
            "independent_evidence_count": self.independent_evidence_count,
            "assisted_success_count": self.assisted_success_count,
            "attempt_count": self.attempt_count,
            "failure_count": self.failure_count,
            "hint_exposure_count": self.hint_exposure_count,
            "latest_outcome": self.latest_outcome,
            "recent_error_refs": self.recent_error_refs,
            "misconception_candidate_refs": self.misconception_candidate_refs,
            "last_practiced_at": self.last_practiced_at,
            "updated_from_event_id": self.updated_from_event_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StudentUnitState":
        return cls(
            student_id=data["student_id"],
            course_id=data.get("course_id", "numerical_analysis"),
            unit_id=data["unit_id"],
            independent_evidence_count=int(data.get("independent_evidence_count", 0)),
            assisted_success_count=int(data.get("assisted_success_count", 0)),
            attempt_count=int(data.get("attempt_count", 0)),
            failure_count=int(data.get("failure_count", 0)),
            hint_exposure_count=int(data.get("hint_exposure_count", 0)),
            latest_outcome=data.get("latest_outcome", "unseen"),
            recent_error_refs=data.get("recent_error_refs", []),
            misconception_candidate_refs=data.get("misconception_candidate_refs", []),
            last_practiced_at=data.get("last_practiced_at", datetime.datetime.now().isoformat()),
            updated_from_event_id=data.get("updated_from_event_id", ""),
        )


@dataclass
class StudentCaseState:
    student_id: str
    course_id: str
    case_id: str
    exposure_count: int = 0
    attempt_count: int = 0
    max_help_used: int = 0
    latest_outcome: str = "unseen"  # unseen | success | assisted_success | failed
    independent_transfer_status: str = "pending"  # pending | verified | struggled
    last_interaction_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "case_id": self.case_id,
            "exposure_count": self.exposure_count,
            "attempt_count": self.attempt_count,
            "max_help_used": self.max_help_used,
            "latest_outcome": self.latest_outcome,
            "independent_transfer_status": self.independent_transfer_status,
            "last_interaction_at": self.last_interaction_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StudentCaseState":
        return cls(
            student_id=data["student_id"],
            course_id=data.get("course_id", "numerical_analysis"),
            case_id=data["case_id"],
            exposure_count=int(data.get("exposure_count", 0)),
            attempt_count=int(data.get("attempt_count", 0)),
            max_help_used=int(data.get("max_help_used", 0)),
            latest_outcome=data.get("latest_outcome", "unseen"),
            independent_transfer_status=data.get("independent_transfer_status", "pending"),
            last_interaction_at=data.get("last_interaction_at", datetime.datetime.now().isoformat()),
        )


class StudentOverlayStore:
    """Stores observable student process events as evidence counts.

    This store deliberately does NOT estimate mastery. Mastery is owned by the
    BKT model in app.memory.mastery; a KT model can later be run over the
    append-only process_events produced here.
    """

    def __init__(self, store: Optional[CourseStore] = None):
        self.store = store
        # key: (student_id, course_id, unit_id) -> StudentUnitState
        self._unit_states: dict[tuple[str, str, str], StudentUnitState] = {}
        # key: (student_id, course_id, case_id) -> StudentCaseState
        self._case_states: dict[tuple[str, str, str], StudentCaseState] = {}
        if store:
            for d in store.load_unit_states():
                s = StudentUnitState.from_dict(d)
                self._unit_states[(s.student_id, s.course_id, s.unit_id)] = s
            for d in store.load_case_states():
                s = StudentCaseState.from_dict(d)
                self._case_states[(s.student_id, s.course_id, s.case_id)] = s

    def get_unit_state(self, student_id: str, course_id: str, unit_id: str) -> StudentUnitState:
        self._reload()
        key = (student_id, course_id, unit_id)
        if key not in self._unit_states:
            self._unit_states[key] = StudentUnitState(
                student_id=student_id,
                course_id=course_id,
                unit_id=unit_id,
            )
        return self._unit_states[key]

    def get_case_state(self, student_id: str, course_id: str, case_id: str) -> StudentCaseState:
        self._reload()
        key = (student_id, course_id, case_id)
        if key not in self._case_states:
            self._case_states[key] = StudentCaseState(
                student_id=student_id,
                course_id=course_id,
                case_id=case_id,
            )
        return self._case_states[key]

    def record_process_event(
        self, event_id: str, student_id: str, course_id: str, unit_ids: list[str],
        case_id: Optional[str] = None, event_type: str = "attempt",
        is_independent: Optional[bool] = None, is_success: Optional[bool] = None,
        help_level: int = 0, misconception_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Validate first, then append and reduce in one transaction.

        Raw observations may have an unknown outcome. Only explicit outcomes
        alter success/failure counts; callers enforce their evidence authority.
        """
        if not event_id or not student_id or not course_id or not 0 <= help_level <= 3:
            raise ValueError("Invalid event identity/help level")
        if len(unit_ids) != len(set(unit_ids)) or len(unit_ids) > 30:
            raise ValueError("Invalid unit ids")
        if event_type not in {"attempt", "hint", "hint_exposed", "revision", "revision_success", "probe", "error", "outcome", "verifier_evidence", "diagnosis", "delivery_failed", "probe_issued"}:
            raise ValueError("Unknown process event")
        if is_success is not None and is_independent is None:
            raise ValueError("Outcome requires independence classification")
        if event_type in {"outcome", "revision_success", "error"} and is_success is None:
            raise ValueError("Outcome event requires a known result")
        payload = {"unit_ids": unit_ids, "case_id": case_id, "event_type": event_type,
                   "is_independent": is_independent, "is_success": is_success,
                   "help_level": help_level, "misconception_id": misconception_id, **(metadata or {})}
        store = self.store
        if store is None:
            from app.knowledge.course_store import CourseStore
            self.store = store = CourseStore()
        with store.transaction():
            previous = store.event_record(event_id)
            if previous:
                if previous["student_id"] != student_id or previous["course_id"] != course_id or previous["event_type"] != event_type or previous["payload"] != payload:
                    raise ValueError("Event id collision")
                return {"status": "duplicate", "event_id": event_id}
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            units = {d["unit_id"]: StudentUnitState.from_dict(d) for d in store.load_unit_states(course_id) if d["student_id"] == student_id}
            cases = {d["case_id"]: StudentCaseState.from_dict(d) for d in store.load_case_states(course_id) if d["student_id"] == student_id}
            hint = event_type in {"hint", "hint_exposed"}
            attempt = event_type in {"attempt", "revision", "probe"}
            changes = hint or attempt or is_success is not None
            for uid in unit_ids if changes else []:
                state = copy.deepcopy(units.get(uid) or StudentUnitState(student_id, course_id, uid))
                state.updated_from_event_id, state.last_practiced_at = event_id, now
                if attempt: state.attempt_count += 1
                if hint: state.hint_exposure_count += 1
                if is_success is True:
                    state.latest_outcome = "success" if is_independent else "assisted_success" if help_level else "observed_success"
                    if is_independent: state.independent_evidence_count += 1
                    elif help_level: state.assisted_success_count += 1
                elif is_success is False:
                    state.latest_outcome = "failed"
                    state.failure_count += 1
                    if misconception_id and misconception_id not in state.misconception_candidate_refs:
                        state.misconception_candidate_refs.append(misconception_id)
                store.upsert_unit_state(student_id, course_id, uid, state.to_dict())
            if case_id and changes:
                state = copy.deepcopy(cases.get(case_id) or StudentCaseState(student_id, course_id, case_id))
                state.last_interaction_at = now
                if attempt: state.attempt_count += 1
                if hint:
                    state.exposure_count += 1
                    state.max_help_used = max(state.max_help_used, help_level)
                if is_success is True:
                    state.latest_outcome = "success" if is_independent else "assisted_success" if help_level else "observed_success"
                    # One independent probe is evidence, not verified transfer ability.
                    if is_independent: state.independent_transfer_status = "probe_observed"
                elif is_success is False:
                    state.latest_outcome = "failed"
                    state.independent_transfer_status = "struggled" if is_independent else state.independent_transfer_status
                store.upsert_case_state(student_id, course_id, case_id, state.to_dict())
            store.append_event(event_id, student_id, course_id, event_type, payload)
        self._reload()
        return {"status": "recorded", "event_id": event_id}

    def _reload(self):
        if self.store:
            self._unit_states = {(d["student_id"], d["course_id"], d["unit_id"]): StudentUnitState.from_dict(d) for d in self.store.load_unit_states()}
            self._case_states = {(d["student_id"], d["course_id"], d["case_id"]): StudentCaseState.from_dict(d) for d in self.store.load_case_states()}

    def get_course_overlay(self, student_id: str, course_id: str) -> dict[str, Any]:
        self._reload()
        unit_map = {
            k[2]: state.to_dict()
            for k, state in self._unit_states.items()
            if k[0] == student_id and k[1] == course_id
        }
        case_map = {
            k[2]: state.to_dict()
            for k, state in self._case_states.items()
            if k[0] == student_id and k[1] == course_id
        }
        return {
            "student_id": student_id,
            "course_id": course_id,
            "units": unit_map,
            "cases": case_map,
        }
