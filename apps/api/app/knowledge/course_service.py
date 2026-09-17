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

                for c_dict in data.get("candidates", []):
                    try:
                        from app.knowledge.candidate_graph import GraphCandidate
                        c = GraphCandidate.from_dict(c_dict)
                        self.candidate_mgr._candidates[c.candidate_id] = c
                    except Exception as ce:
                        logger.warning(f"Failed to load candidate {c_dict.get('candidate_id')}: {ce}")
            except Exception as e:
                logger.error(f"Failed to load course pack from {pack_file}: {e}")
        else:
            logger.warning("No course pack file found for initialization.")

        # Seed initial dynamic evolution candidates if none loaded
        if not self.candidate_mgr._candidates:
            self._seed_default_candidates()

    def _seed_default_candidates(self) -> None:
        from app.knowledge.candidate_graph import CandidateType, CandidateStatus, GraphCandidate
        default_candidates = [
            GraphCandidate(
                candidate_id="CAND_SECANT_METHOD",
                candidate_type=CandidateType.NEW_UNIT.value,
                course_id=self.course_id,
                payload={
                    "id": "NA_SECANT",
                    "title": "割线法 / 弦截法 (Secant Method)",
                    "type": "algorithm",
                    "content": "用两点割线的斜率代替切线导数 f'(x_k)，避免解析求导。其收敛阶为黄金分割比 p ≈ 1.618，属于超线性收敛。每次迭代仅需计算一次函数值。",
                    "latex": "x_{k+1} = x_k - f(x_k) \\frac{x_k - x_{k-1}}{f(x_k) - f(x_{k-1})}",
                    "keywords": ["割线法", "弦截法", "Secant", "超线性收敛", "避免导数"],
                    "difficulty": 3,
                    "scope_level": "core",
                    "teaching_role": "core"
                },
                proposed_by="student_query_cluster",
                support_count=14,
                evidence_refs=["query_cluster_202609_01", "student_dialogue_#849", "exam_review_2025"],
                status=CandidateStatus.PENDING.value
            ),
            GraphCandidate(
                candidate_id="CAND_NEWTON_MODIFIED",
                candidate_type=CandidateType.NEW_UNIT.value,
                course_id=self.course_id,
                payload={
                    "id": "NA_SIMPLIFIED_NEWTON",
                    "title": "简化牛顿法 / 平行弦法 (Modified Newton Method)",
                    "type": "algorithm",
                    "content": "在迭代全过程中固定使用初始导数值 f'(x_0) 代替每次更新的 f'(x_k)。每步迭代只需计算函数值，大幅降低导数求值开销，但收敛速度降为局部线性收敛。",
                    "latex": "x_{k+1} = x_k - \\frac{f(x_k)}{f'(x_0)}",
                    "keywords": ["简化牛顿法", "平行弦法", "固定斜率", "线性收敛"],
                    "difficulty": 3,
                    "scope_level": "core",
                    "teaching_role": "extension"
                },
                proposed_by="teacher",
                support_count=5,
                evidence_refs=["textbook_ch2_sec3", "assignment_hw3_p2"],
                status=CandidateStatus.PENDING.value
            ),
            GraphCandidate(
                candidate_id="CAND_ALIAS_TANGENT_METHOD",
                candidate_type=CandidateType.NEW_ALIAS.value,
                course_id=self.course_id,
                payload={
                    "target_id": "NA_NEWTON",
                    "alias": "切线法",
                    "note": "多位同学在提问中将牛顿迭代法称为“切线法”，建议合并为 NA_NEWTON 规范别名。"
                },
                proposed_by="student_query_cluster",
                support_count=28,
                evidence_refs=["query_cluster_202609_02", "dialogue_#1022", "dialogue_#1104"],
                status=CandidateStatus.PENDING.value
            ),
            GraphCandidate(
                candidate_id="CAND_CASE_INITIAL_DIVERGENCE",
                candidate_type=CandidateType.NEW_CASE.value,
                course_id=self.course_id,
                payload={
                    "case_id": "CASE_NEWTON_OSCILLATION_CYCLE",
                    "course_id": self.course_id,
                    "title": "牛顿法初值选取导致的周期振荡案例",
                    "task_type": "debug_task",
                    "learning_objectives": ["引导学生诊断牛顿法在特定非凸函数初值导致死循环振荡的原因"],
                    "concept_ids": ["NA_NEWTON", "NA_LOCAL_CONVERGENCE", "NA_STOPPING_CRITERIA"],
                    "required_condition_ids": ["initial_guess_in_convergence_ball", "cycle_detection"],
                    "reasoning_signature": ["检查导数是否过小", "检测是否在两点间振荡", "建议使用二分法试探合适初值"],
                    "accepted_variants": [
                        "为什么牛顿法算出来一直在几个数之间跳",
                        "牛顿迭代法死循环怎么排查",
                        "初值怎么选才能保证牛顿法收敛"
                    ],
                    "disclosure_policy": "scaffolded"
                },
                proposed_by="teacher",
                support_count=8,
                evidence_refs=["office_hour_case_2026", "midterm_common_mistake"],
                status=CandidateStatus.PENDING.value
            ),
            GraphCandidate(
                candidate_id="CAND_AITKEN_ACCELERATION",
                candidate_type=CandidateType.NEW_UNIT.value,
                course_id=self.course_id,
                payload={
                    "id": "NA_AITKEN_ACCELERATION",
                    "title": "埃特金加速法 (Aitken Acceleration)",
                    "type": "algorithm",
                    "content": "通过利用三个连续迭代值的外推，提高线性收敛迭代序列的收敛速度。",
                    "latex": "\\bar{x}_k = x_k - \\frac{(x_{k+1} - x_k)^2}{x_{k+2} - 2x_{k+1} + x_k}",
                    "difficulty": 4,
                    "scope_level": "extension"
                },
                proposed_by="teacher",
                support_count=3,
                evidence_refs=["syllabus_expansion"],
                status=CandidateStatus.APPROVED.value,
                reviewer_id="prof_luojia",
                review_note="同意纳入扩展知识点，收敛阶由线性加速至更高阶。"
            )
        ]
        for c in default_candidates:
            self.candidate_mgr._candidates[c.candidate_id] = c


# Global cache of CourseServices
_course_services: dict[str, CourseService] = {}


def get_course_service(course_id: str = "numerical_analysis") -> CourseService:
    if course_id not in _course_services:
        _course_services[course_id] = CourseService(course_id=course_id)
    return _course_services[course_id]


def reset_course_services() -> None:
    _course_services.clear()
