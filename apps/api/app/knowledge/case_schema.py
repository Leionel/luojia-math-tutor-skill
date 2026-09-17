from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskType(str, Enum):
    CONCEPT_EXPLANATION = "concept_explanation"
    CONVERGENCE_ANALYSIS = "convergence_analysis"
    DERIVATION = "derivation"
    ERROR_DEBUGGING = "error_debugging"
    CODE_TASK = "code_task"
    WORKED_EXAMPLE = "worked_example"
    INDEPENDENT_PRACTICE = "independent_practice"
    ASSESSMENT = "assessment"


class DisclosurePolicy(str, Enum):
    DIRECT = "direct"  # Can explain concepts directly
    SCAFFOLDED = "scaffolded"  # Step-by-step guidance, withhold final step
    WITHHELD = "withheld"  # Strict answer withholding (assessments/probes)
    CONCEPTUAL_ONLY = "conceptual_only"  # Only allow discussion of theory/conditions


class CaseDecision(str, Enum):
    SAME_CASE = "SAME_CASE"
    VARIANT_OF_CASE = "VARIANT_OF_CASE"
    RELATED_CASE = "RELATED_CASE"
    NEW_CASE = "NEW_CASE"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class TeachingCase:
    case_id: str
    course_id: str
    title: str
    task_type: str = TaskType.CONCEPT_EXPLANATION.value
    course_version: str = "v1.0"
    learning_objectives: list[str] = field(default_factory=list)
    concept_ids: list[str] = field(default_factory=list)
    required_condition_ids: list[str] = field(default_factory=list)
    related_misconception_ids: list[str] = field(default_factory=list)
    reasoning_signature: list[str] = field(default_factory=list)
    accepted_variants: list[str] = field(default_factory=list)
    allowed_alternatives: list[str] = field(default_factory=list)
    forbidden_shortcuts: list[str] = field(default_factory=list)
    diagnostic_probes: list[dict[str, Any]] = field(default_factory=list)
    possible_actions: list[dict[str, Any]] = field(default_factory=list)
    disclosure_policy: str = DisclosurePolicy.SCAFFOLDED.value
    oracle_spec_ids: list[str] = field(default_factory=list)
    benchmark_family_id: str = ""
    provenance: str = "teacher_curated"  # teacher_curated | student_cluster | llm_extracted
    review_status: str = "verified"  # draft | verified | deprecated

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "course_id": self.course_id,
            "title": self.title,
            "task_type": self.task_type,
            "course_version": self.course_version,
            "learning_objectives": self.learning_objectives,
            "concept_ids": self.concept_ids,
            "required_condition_ids": self.required_condition_ids,
            "related_misconception_ids": self.related_misconception_ids,
            "reasoning_signature": self.reasoning_signature,
            "accepted_variants": self.accepted_variants,
            "allowed_alternatives": self.allowed_alternatives,
            "forbidden_shortcuts": self.forbidden_shortcuts,
            "diagnostic_probes": self.diagnostic_probes,
            "possible_actions": self.possible_actions,
            "disclosure_policy": self.disclosure_policy,
            "oracle_spec_ids": self.oracle_spec_ids,
            "benchmark_family_id": self.benchmark_family_id,
            "provenance": self.provenance,
            "review_status": self.review_status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeachingCase":
        return cls(
            case_id=data["case_id"],
            course_id=data.get("course_id", "numerical_analysis"),
            title=data.get("title", ""),
            task_type=data.get("task_type", TaskType.CONCEPT_EXPLANATION.value),
            course_version=data.get("course_version", "v1.0"),
            learning_objectives=data.get("learning_objectives", []),
            concept_ids=data.get("concept_ids", []),
            required_condition_ids=data.get("required_condition_ids", []),
            related_misconception_ids=data.get("related_misconception_ids", []),
            reasoning_signature=data.get("reasoning_signature", []),
            accepted_variants=data.get("accepted_variants", []),
            allowed_alternatives=data.get("allowed_alternatives", []),
            forbidden_shortcuts=data.get("forbidden_shortcuts", []),
            diagnostic_probes=data.get("diagnostic_probes", []),
            possible_actions=data.get("possible_actions", []),
            disclosure_policy=data.get("disclosure_policy", DisclosurePolicy.SCAFFOLDED.value),
            oracle_spec_ids=data.get("oracle_spec_ids", []),
            benchmark_family_id=data.get("benchmark_family_id", ""),
            provenance=data.get("provenance", "teacher_curated"),
            review_status=data.get("review_status", "verified"),
        )


@dataclass
class CaseMatchResult:
    decision: CaseDecision
    matched_case_id: Optional[str] = None
    matched_case: Optional[TeachingCase] = None
    confidence: float = 0.0
    candidate_cases: list[dict[str, Any]] = field(default_factory=list)
    concept_anchor_ids: list[str] = field(default_factory=list)
    difference_axes: list[str] = field(default_factory=list)
    diagnostic_probe: Optional[dict[str, Any]] = None
    review_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "matched_case_id": self.matched_case_id,
            "matched_case": self.matched_case.to_dict() if self.matched_case else None,
            "confidence": round(self.confidence, 4),
            "candidate_cases": self.candidate_cases,
            "concept_anchor_ids": self.concept_anchor_ids,
            "difference_axes": self.difference_axes,
            "diagnostic_probe": self.diagnostic_probe,
            "review_required": self.review_required,
        }
