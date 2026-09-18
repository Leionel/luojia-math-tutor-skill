from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ScopeLevel(str, Enum):
    CORE = "core"  # 课程大纲内必须掌握的核心知识
    PREREQUISITE = "prerequisite"  # 理解核心所需的前置知识（如微积分定理）
    EXTENSION = "extension"  # 课程内相关拓展，允许在学生主动追问时展开
    EXTERNAL = "external"  # 知识图谱知晓其存在，但默认不主动展开的域外知识
    UNCLASSIFIED = "unclassified"  # 未经教师审核分类的知识：可作候选证据，不可权威教学


@dataclass
class BlockedUnit:
    unit_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"unit_id": self.unit_id, "reason": self.reason}


@dataclass
class BoundaryDecision:
    """Typed boundary verdict for a set of units (consumed by prompt_builder)."""

    core_units: list[str] = field(default_factory=list)
    prerequisite_units: list[str] = field(default_factory=list)
    extension_units: list[str] = field(default_factory=list)
    unclassified_units: list[str] = field(default_factory=list)
    blocked_units: list[BlockedUnit] = field(default_factory=list)
    crossing_type: Optional[str] = None

    @property
    def has_boundary_crossing(self) -> bool:
        return bool(self.blocked_units or self.unclassified_units)

    def to_dict(self) -> dict[str, Any]:
        return {
            "core_units": self.core_units,
            "prerequisite_units": self.prerequisite_units,
            "extension_units": self.extension_units,
            "unclassified_units": self.unclassified_units,
            "blocked_units": [b.to_dict() for b in self.blocked_units],
            "has_boundary_crossing": self.has_boundary_crossing,
            "crossing_type": self.crossing_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BoundaryDecision":
        return cls(
            core_units=list(data.get("core_units", [])),
            prerequisite_units=list(data.get("prerequisite_units", [])),
            extension_units=list(data.get("extension_units", [])),
            unclassified_units=list(data.get("unclassified_units", [])),
            blocked_units=[
                b if isinstance(b, BlockedUnit) else BlockedUnit(**b)
                for b in data.get("blocked_units", [])
            ],
            crossing_type=data.get("crossing_type"),
        )


@dataclass
class BoundaryPolicy:
    course_id: str
    unit_id: str
    scope_level: str = ScopeLevel.CORE.value
    allowed_task_modes: list[str] = field(default_factory=lambda: [
        "concept_explanation", "convergence_analysis", "derivation", "error_debugging", "code_task"
    ])
    max_expansion_depth: int = 1
    teacher_note: str = ""
    source: str = "curriculum_syllabus"

    def to_dict(self) -> dict[str, Any]:
        return {
            "course_id": self.course_id,
            "unit_id": self.unit_id,
            "scope_level": self.scope_level,
            "allowed_task_modes": self.allowed_task_modes,
            "max_expansion_depth": self.max_expansion_depth,
            "teacher_note": self.teacher_note,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BoundaryPolicy":
        return cls(
            course_id=data.get("course_id", "numerical_analysis"),
            unit_id=data["unit_id"],
            scope_level=data.get("scope_level", ScopeLevel.CORE.value),
            allowed_task_modes=data.get("allowed_task_modes", [
                "concept_explanation", "convergence_analysis", "derivation", "error_debugging", "code_task"
            ]),
            max_expansion_depth=data.get("max_expansion_depth", 1),
            teacher_note=data.get("teacher_note", ""),
            source=data.get("source", "curriculum_syllabus"),
        )


class BoundaryChecker:
    """Enforces curriculum boundary constraints during graph retrieval and expansion.

    Fail-closed: units without a policy are UNCLASSIFIED. They may appear as
    candidate evidence but must not be used for authoritative teaching until a
    teacher assigns them a scope.
    """

    def __init__(self, policies: Optional[dict[str, BoundaryPolicy]] = None):
        self.policies = policies or {}

    def set_policy(self, policy: BoundaryPolicy) -> None:
        self.policies[policy.unit_id] = policy

    def get_policy(self, unit_id: str) -> Optional[BoundaryPolicy]:
        return self.policies.get(unit_id)

    def get_scope_level(self, unit_id: str) -> ScopeLevel:
        policy = self.policies.get(unit_id)
        if not policy:
            return ScopeLevel.UNCLASSIFIED
        try:
            return ScopeLevel(policy.scope_level)
        except ValueError:
            return ScopeLevel.UNCLASSIFIED

    def can_expand(
        self,
        unit_id: str,
        current_depth: int,
        task_mode: str = "concept_explanation",
        allow_extension: bool = True
    ) -> tuple[bool, str]:
        """Check whether expansion to `unit_id` at `current_depth` is allowed."""
        policy = self.policies.get(unit_id)
        if not policy:
            return False, "unclassified_requires_teacher_review"

        scope = policy.scope_level
        if scope == ScopeLevel.EXTERNAL.value:
            return False, "external_boundary_blocked"

        if scope == ScopeLevel.UNCLASSIFIED.value:
            return False, "unclassified_requires_teacher_review"

        if scope == ScopeLevel.EXTENSION.value and not allow_extension:
            return False, "extension_not_requested"

        if task_mode and policy.allowed_task_modes and task_mode not in policy.allowed_task_modes:
            return False, f"task_mode_{task_mode}_not_allowed"

        if current_depth > policy.max_expansion_depth:
            return False, f"depth_{current_depth}_exceeds_max_{policy.max_expansion_depth}"

        return True, "allowed"

    def filter_units(
        self,
        unit_ids: list[str],
        allow_extension: bool = True,
        allow_prerequisite: bool = True,
        allow_external: bool = False,
        allow_unclassified: bool = False,
    ) -> list[str]:
        filtered = []
        for uid in unit_ids:
            policy = self.policies.get(uid)
            if not policy:
                if allow_unclassified:
                    filtered.append(uid)
                continue
            scope = policy.scope_level
            if scope == ScopeLevel.CORE.value:
                filtered.append(uid)
            elif scope == ScopeLevel.PREREQUISITE.value and allow_prerequisite:
                filtered.append(uid)
            elif scope == ScopeLevel.EXTENSION.value and allow_extension:
                filtered.append(uid)
            elif scope == ScopeLevel.EXTERNAL.value and allow_external:
                filtered.append(uid)
        return filtered

    def inspect_boundary_decision(
        self,
        target_unit_ids: list[str],
        allow_extension: bool = False
    ) -> BoundaryDecision:
        """Summarize boundary status for retrieval pack."""
        decision = BoundaryDecision()

        for uid in target_unit_ids:
            scope = self.get_scope_level(uid)
            if scope == ScopeLevel.CORE:
                decision.core_units.append(uid)
            elif scope == ScopeLevel.PREREQUISITE:
                decision.prerequisite_units.append(uid)
            elif scope == ScopeLevel.EXTENSION:
                if allow_extension:
                    decision.extension_units.append(uid)
                else:
                    decision.blocked_units.append(BlockedUnit(uid, "extension_unrequested"))
            elif scope == ScopeLevel.EXTERNAL:
                decision.blocked_units.append(BlockedUnit(uid, "external_boundary"))
            elif scope == ScopeLevel.UNCLASSIFIED:
                decision.unclassified_units.append(uid)

        if decision.blocked_units:
            reasons = {b.reason for b in decision.blocked_units}
            decision.crossing_type = "mixed" if len(reasons) > 1 else reasons.pop()
        elif decision.unclassified_units:
            decision.crossing_type = "unclassified_pending_review"

        return decision
