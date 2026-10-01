import json
import hashlib
import threading
import logging
from pathlib import Path

from app.config import get_settings
from app.knowledge.course_store import CourseStore
from app.knowledge.graph_repository import CourseGraphRepository
from app.knowledge.case_matcher import TeachingCaseMatcher
from app.knowledge.candidate_graph import CandidateManager
from app.knowledge.student_overlay import StudentOverlayStore
from app.knowledge.graph_review import GraphReviewService

logger = logging.getLogger(__name__)


class CourseService:
    """Service encapsulating the Course Graph, Case Matcher, Review, and Student Overlay."""

    def __init__(self, course_id: str = "numerical_analysis", *, store: CourseStore | None = None):
        if not course_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in course_id):
            raise ValueError("Invalid course id")
        self.course_id = course_id
        settings = get_settings()
        # Persistence is opt-in via COURSE_STORE_PATH so tests stay in-memory.
        self.store = store if store is not None else CourseStore(settings.course_store_path or None)
        self.graph_repo = CourseGraphRepository(course_id=course_id)
        self.candidate_mgr = CandidateManager(store=self.store)
        self.overlay_store = StudentOverlayStore(store=self.store)
        self.case_matcher = TeachingCaseMatcher(self.graph_repo.case_repo)

        self._load_default_course_pack()
        self.review_service = GraphReviewService(self.graph_repo, self.candidate_mgr, store=self.store)

    def _load_default_course_pack(self) -> None:
        saved = self.store.load_graph(self.course_id)
        if saved:
            self.graph_repo.load_from_course_pack(saved["data"])
            return
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
                saved = self.store.initialize_graph(self.course_id, self.graph_repo.to_course_pack(), hashlib.sha256(pack_file.read_bytes()).hexdigest())
                self.graph_repo.replace_from_course_pack(saved["data"])
                logger.info(f"Loaded course pack from {pack_file}")
            except Exception as e:
                logger.error(f"Failed to load course pack from {pack_file}: {e}")
                raise
        else:
            logger.warning("No course pack file found for initialization.")


# Global cache of CourseServices
_course_services: dict[str, CourseService] = {}
_service_lock = threading.RLock()


def get_course_service(course_id: str = "numerical_analysis") -> CourseService:
    with _service_lock:
        if course_id not in _course_services:
            _course_services[course_id] = CourseService(course_id=course_id)
        return _course_services[course_id]


def reset_course_services() -> None:
    _course_services.clear()
