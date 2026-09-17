import logging
from pathlib import Path
from typing import Any, Optional

from app.knowledge.case_schema import TeachingCase

logger = logging.getLogger(__name__)


class TeachingCaseRepository:
    """Repository for managing course Teaching Cases."""

    def __init__(self, cases: Optional[list[TeachingCase]] = None):
        self._cases: dict[str, TeachingCase] = {}
        self._course_index: dict[str, list[str]] = {}
        self._concept_index: dict[str, list[str]] = {}
        if cases:
            for case in cases:
                self.add_case(case)

    def add_case(self, case: TeachingCase) -> None:
        self._cases[case.case_id] = case

        # Course index
        if case.course_id not in self._course_index:
            self._course_index[case.course_id] = []
        if case.case_id not in self._course_index[case.course_id]:
            self._course_index[case.course_id].append(case.case_id)

        # Concept index
        for cid in case.concept_ids:
            if cid not in self._concept_index:
                self._concept_index[cid] = []
            if case.case_id not in self._concept_index[cid]:
                self._concept_index[cid].append(case.case_id)

    def get_case(self, case_id: str) -> Optional[TeachingCase]:
        return self._cases.get(case_id)

    def list_cases(
        self,
        course_id: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> list[TeachingCase]:
        if course_id and course_id in self._course_index:
            case_ids = self._course_index[course_id]
            results = [self._cases[cid] for cid in case_ids if cid in self._cases]
        else:
            results = list(self._cases.values())

        if task_type:
            results = [c for c in results if c.task_type == task_type]

        return results

    def find_by_concept(self, concept_id: str) -> list[TeachingCase]:
        case_ids = self._concept_index.get(concept_id, [])
        return [self._cases[cid] for cid in case_ids if cid in self._cases]

    def count(self) -> int:
        return len(self._cases)
