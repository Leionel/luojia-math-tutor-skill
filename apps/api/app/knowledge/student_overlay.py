import datetime
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StudentUnitState:
    student_id: str
    course_id: str
    unit_id: str
    mastery_estimate: float = 0.5
    independent_evidence_count: int = 0
    assisted_success_count: int = 0
    recent_error_refs: list[str] = field(default_factory=list)
    misconception_candidate_refs: list[str] = field(default_factory=list)
    last_practiced_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_from_event_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "unit_id": self.unit_id,
            "mastery_estimate": round(self.mastery_estimate, 3),
            "independent_evidence_count": self.independent_evidence_count,
            "assisted_success_count": self.assisted_success_count,
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
            mastery_estimate=float(data.get("mastery_estimate", 0.5)),
            independent_evidence_count=int(data.get("independent_evidence_count", 0)),
            assisted_success_count=int(data.get("assisted_success_count", 0)),
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
    """Stores and reduces observable student process events into lightweight graph overlays."""

    def __init__(self):
        # key: (student_id, course_id, unit_id) -> StudentUnitState
        self._unit_states: dict[tuple[str, str, str], StudentUnitState] = {}
        # key: (student_id, course_id, case_id) -> StudentCaseState
        self._case_states: dict[tuple[str, str, str], StudentCaseState] = {}

    def get_unit_state(self, student_id: str, course_id: str, unit_id: str) -> StudentUnitState:
        key = (student_id, course_id, unit_id)
        if key not in self._unit_states:
            self._unit_states[key] = StudentUnitState(
                student_id=student_id,
                course_id=course_id,
                unit_id=unit_id,
            )
        return self._unit_states[key]

    def get_case_state(self, student_id: str, course_id: str, case_id: str) -> StudentCaseState:
        key = (student_id, course_id, case_id)
        if key not in self._case_states:
            self._case_states[key] = StudentCaseState(
                student_id=student_id,
                course_id=course_id,
                case_id=case_id,
            )
        return self._case_states[key]

    def record_process_event(
        self,
        event_id: str,
        student_id: str,
        course_id: str,
        unit_ids: list[str],
        case_id: Optional[str] = None,
        event_type: str = "attempt",  # attempt | hint | revision_success | error
        is_independent: bool = True,
        is_success: bool = True,
        help_level: int = 0,
        misconception_id: Optional[str] = None
    ) -> None:
        now = datetime.datetime.now().isoformat()

        # Update case state
        if case_id:
            case_state = self.get_case_state(student_id, course_id, case_id)
            case_state.exposure_count += 1
            if event_type == "attempt":
                case_state.attempt_count += 1
            case_state.max_help_used = max(case_state.max_help_used, help_level)
            case_state.last_interaction_at = now
            if is_success:
                case_state.latest_outcome = "success" if is_independent else "assisted_success"
                if is_independent and case_state.independent_transfer_status != "verified":
                    case_state.independent_transfer_status = "verified"
            else:
                case_state.latest_outcome = "failed"
                case_state.independent_transfer_status = "struggled"

        # Update unit states
        for uid in unit_ids:
            unit_state = self.get_unit_state(student_id, course_id, uid)
            unit_state.last_practiced_at = now
            unit_state.updated_from_event_id = event_id

            if is_success:
                if is_independent:
                    unit_state.independent_evidence_count += 1
                    # BKT-like increment toward mastery
                    unit_state.mastery_estimate = min(1.0, unit_state.mastery_estimate + 0.15)
                else:
                    unit_state.assisted_success_count += 1
                    unit_state.mastery_estimate = min(1.0, unit_state.mastery_estimate + 0.05)
            else:
                unit_state.mastery_estimate = max(0.0, unit_state.mastery_estimate - 0.10)
                if misconception_id and misconception_id not in unit_state.misconception_candidate_refs:
                    unit_state.misconception_candidate_refs.append(misconception_id)

    def get_course_overlay(self, student_id: str, course_id: str) -> dict[str, Any]:
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
