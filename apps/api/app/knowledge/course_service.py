from functools import lru_cache
import json
import logging
from pathlib import Path
from typing import Optional

from app.knowledge.graph_repository import CourseGraphRepository
from app.knowledge.case_matcher import TeachingCaseMatcher
from app.knowledge.candidate_graph import CandidateManager
from app.knowledge.student_overlay import StudentOverlayStore
from app.knowledge.graph_review import GraphReviewService

logger = logging.getLogger(__name__)


class CourseService:
    """Service encapsulating the Course Graph, Case Matcher, Review, and Student Overlay."""

    def __init__(self, course_id: str = "numerical_analysis"):
        self.course_id = course_id
        self.graph_repo = CourseGraphRepository(course_id=course_id)
        self.candidate_mgr = CandidateManager()
        self.overlay_store = StudentOverlayStore()
        self.review_service = GraphReviewService(self.graph_repo, self.candidate_mgr)
        self.case_matcher = TeachingCaseMatcher(self.graph_repo.case_repo)

        self._load_default_course_pack()

    def _load_default_course_pack(self) -> None:
        current = Path(__file__).resolve()
        pack_candidates = [
            current.parents[4] / "data" / "course_packs" / f"{self.course_id}_root_finding.json",
            current.parents[3] / "data" / "course_packs" / f"{self.course_id}_root_finding.json",
            Path.cwd() / "data" / "course_packs" / f"{self.course_id}_root_finding.json",
            Path.cwd().parent.parent / "data" / "course_packs" / f"{self.course_id}_root_finding.json",
        ]
        pack_file = None
        for p in pack_candidates:
            if p.exists():
                pack_file = p
                break

        if pack_file:
            try:
                with open(pack_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.graph_repo.load_from_course_pack(data)
                logger.info(f"Loaded course pack from {pack_file}")
            except Exception as e:
                logger.error(f"Failed to load course pack from {pack_file}: {e}")
        else:
            logger.warning("No course pack file found for initialization.")


# Global cache of CourseServices
_course_services: dict[str, CourseService] = {}


def get_course_service(course_id: str = "numerical_analysis") -> CourseService:
    if course_id not in _course_services:
        _course_services[course_id] = CourseService(course_id=course_id)
    return _course_services[course_id]


def reset_course_services() -> None:
    _course_services.clear()
