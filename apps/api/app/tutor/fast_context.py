import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.config import Settings, get_settings
from app.knowledge.schema import KnowledgeHit, EvidencePack
from app.knowledge.search import search_evidence_pack
from app.knowledge.concepts import extract_explicit_concepts
from app.math_tools.step_checker import check_step
from app.math_tools.verifier import VerifyResult
from app.memory.mastery import mastery_label, update_mastery
from app.memory.repository import Repository
from app.tutor.fast_path import VerificationMode
from app.tutor.hint_policy import decide_hint_level
from app.tutor.intent_router import Intent
from app.tutor.misconception import Mistake

logger = logging.getLogger(__name__)

LocalSearch = Callable[
    [str, str | None, int],
    Awaitable[EvidencePack],
]


@dataclass
class FastContext:
    history: list[dict[str, str]]
    evidence_pack: EvidencePack | None
    hits: list[KnowledgeHit]
    document_chunks: list[str]
    concepts: list[str]
    concept_items: list[dict[str, Any]]
    verifier_result: VerifyResult
    mistake: Mistake | None
    mastery_score: float
    mastery_delta: float
    mastery_label_str: str
    hint_level: int
    metrics: dict[str, float | int | str | bool]
    prerequisite_hints: list[dict[str, str]] = field(default_factory=list)


class FastContextCollector:
    def __init__(
        self,
        repository: Repository,
        timeout_seconds: float = 0.35,
        local_search: LocalSearch = search_evidence_pack,
        settings: Settings | None = None,
    ):
        self.repository = repository
        self.timeout_seconds = timeout_seconds
        self.local_search = local_search
        self.settings = settings or get_settings()

    async def collect(self, state: dict[str, Any]) -> FastContext:
        started = time.perf_counter()
        (
            history,
            document_id,
            previous_concepts,
            previous_concept_items,
        ) = await asyncio.to_thread(
            self._prepare_session,
            state["user_id"],
            state["session_id"],
            state["message"],
        )

        tasks = {
            asyncio.create_task(self._collect_local_hits(state)): "hits",
            asyncio.create_task(
                self._collect_document_chunks(document_id, state["message"])
            ): "document_chunks",
            asyncio.create_task(self._collect_symbolic_result(state)): "symbolic",
        }
        done, pending = await asyncio.wait(
            tasks,
            timeout=self.timeout_seconds,
        )

        results: dict[str, Any] = {}
        durations: dict[str, float] = {}
        for task in done:
            name = tasks[task]
            try:
                value, duration_ms = task.result()
                results[name] = value
                durations[name] = duration_ms
            except Exception:
                logger.exception("Fast context task %s failed", name)

        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        pack = results.get("hits", None)
        hits = pack.direct_hits + pack.graph_hits if pack else []
        document_chunks = results.get("document_chunks", [])
        verifier_result, mistake = results.get(
            "symbolic",
            (
                VerifyResult(
                    False,
                    None,
                    "本轮未获得确定性的自动验证结果。",
                ),
                None,
            ),
        )
        concepts = self._derive_concepts(
            state["message"],
            hits,
            mistake,
            previous_concepts,
        )
        concept_items = self._build_concept_items(
            message=state["message"],
            concepts=concepts,
            hits=hits,
            mistake=mistake,
            previous_items=previous_concept_items,
            assessed=(
                state.get("intent") is Intent.CHECK_STUDENT_STEP
                and verifier_result.verified
                and verifier_result.is_correct is not None
            ),
        )
        learning_state = {
            **state,
            "hits": hits,
        }
        mastery = await asyncio.to_thread(
            self._finalize_learning_state,
            learning_state,
            concepts,
            verifier_result,
            mistake,
        )

        metrics: dict[str, float | int | str | bool] = {
            "fast_context_ms": round(
                (time.perf_counter() - started) * 1000,
                2,
            ),
            "local_rag_ms": round(durations.get("hits", 0.0), 2),
            "symbolic_verify_ms": round(durations.get("symbolic", 0.0), 2),
            "context_timed_out": bool(pending),
        }
        return FastContext(
            history=history,
            evidence_pack=pack,
            hits=hits,
            document_chunks=document_chunks,
            concepts=concepts,
            concept_items=concept_items,
            verifier_result=verifier_result,
            mistake=mistake,
            mastery_score=mastery["mastery_score"],
            mastery_delta=mastery["mastery_delta"],
            mastery_label_str=mastery["mastery_label_str"],
            hint_level=mastery["hint_level"],
            metrics=metrics,
            prerequisite_hints=mastery.get("prerequisite_hints", []),
        )

    def _prepare_session(
        self,
        user_id: str,
        session_id: str,
        message: str,
    ) -> tuple[
        list[dict[str, str]],
        str | None,
        list[str],
        list[dict[str, Any]],
    ]:
        self.repository.ensure_user(user_id)
        db_messages = self.repository.list_messages(session_id)
        history = [
            {"role": item["role"], "content": item["content"]}
            for item in db_messages
        ]
        previous_concepts: list[str] = []
        previous_concept_items: list[dict[str, Any]] = []
        for item in reversed(db_messages):
            learning_meta = item.get("learning_meta") or {}
            concepts = learning_meta.get("concepts") or []
            if item.get("role") == "assistant" and concepts:
                previous_concepts = concepts
                previous_concept_items = learning_meta.get("concept_items") or []
                break
        self.repository.add_message(session_id, "user", message)
        sessions = self.repository.list_sessions(user_id)
        current_session = next(
            (item for item in sessions if item["id"] == session_id),
            None,
        )
        document_id = (
            current_session.get("document_id")
            if current_session
            else None
        )
        return history, document_id, previous_concepts, previous_concept_items

    async def _collect_local_hits(
        self,
        state: dict[str, Any],
    ) -> tuple[EvidencePack | None, float]:
        started = time.perf_counter()
        pack = None
        # 1. Try Course Graph 2.0 evidence builder first for Numerical Analysis or general root-finding
        try:
            from app.knowledge.evidence_builder import CourseEvidenceBuilder
            builder = CourseEvidenceBuilder(course_id="numerical_analysis")
            course_pack = await asyncio.to_thread(
                builder.build_evidence_pack,
                query=state["message"],
                student_id=state.get("user_id"),
                task_mode=state.get("mode"),
                allow_extension=False,
            )
            if course_pack and (course_pack.matched_case or course_pack.concept_anchors):
                pack = course_pack
        except Exception as exc:
            logger.debug("CourseEvidenceBuilder check failed or bypassed: %s", exc)

        # 2. Fallback to standard local search if not matched to Course Graph 2.0
        if not pack:
            try:
                pack = await self.local_search(
                    state["message"],
                    state.get("detected_subject") or state.get("subject"),
                    5,
                )
            except Exception:
                logger.exception("Local knowledge search failed")
                pack = None
        return pack, (time.perf_counter() - started) * 1000

    async def _collect_document_chunks(
        self,
        document_id: str | None,
        message: str,
    ) -> tuple[list[str], float]:
        started = time.perf_counter()
        if not document_id:
            return [], 0.0
        try:
            chunks = await asyncio.to_thread(
                self.repository.search_document_chunks,
                document_id,
                message,
                3,
            )
        except Exception:
            logger.exception("Document chunk search failed")
            chunks = []
        return chunks, (time.perf_counter() - started) * 1000

    async def _collect_symbolic_result(
        self,
        state: dict[str, Any],
    ) -> tuple[tuple[VerifyResult, Mistake | None], float]:
        started = time.perf_counter()
        if state.get("verification_mode") != VerificationMode.SYMBOLIC.value:
            result = (
                VerifyResult(False, None, "本轮无需自动符号验证。"),
                None,
            )
        else:
            try:
                result = await asyncio.to_thread(
                    check_step,
                    state["message"],
                )
            except Exception:
                logger.exception("Symbolic step checking failed")
                result = (
                    VerifyResult(False, None, "自动符号验证失败。"),
                    None,
                )
        return result, (time.perf_counter() - started) * 1000

    @staticmethod
    def _classify_integral(message: str) -> str | None:
        compact = message.replace(" ", "").lower()
        if "∫" not in compact and "\\int" not in compact:
            return None
        if re.search(r"(?:∫|\\int)_?\{?[^}]*\}?\^\{?[^}]*\}?", compact):
            return "定积分"
        if any(marker in compact for marker in ("sin", "cos", "tan", "正弦", "余弦")):
            return "三角函数积分"
        if any(marker in compact for marker in ("e^", "exp", "指数")):
            return "指数函数积分"
        if re.search(r"x(?:\^|[¹²³⁴⁵⁶⁷⁸⁹])", compact):
            return "幂函数积分"
        return "积分"

    @staticmethod
    def _derive_concepts(
        message: str,
        hits: list[KnowledgeHit],
        mistake: Mistake | None,
        previous_concepts: list[str] | None = None,
    ) -> list[str]:
        previous_concepts = previous_concepts or []
        explicit_concepts = extract_explicit_concepts(message)
        is_short_follow_up = (
            len(message.strip()) <= 18
            or any(
                marker in message
                for marker in ("继续", "然后呢", "好的", "明白", "下一步")
            )
        )
        if explicit_concepts:
            concepts = [*explicit_concepts, *previous_concepts]
        elif previous_concepts and is_short_follow_up:
            concepts = list(previous_concepts)
        else:
            concepts = [
                hit.item.concept_zh
                for hit in hits[:3]
                if hit.item.concept_zh
            ]
        integral_concept = FastContextCollector._classify_integral(message)
        if not concepts and integral_concept:
            concepts.append(integral_concept)
        if mistake and mistake.concept not in concepts:
            concepts.insert(0, mistake.concept)
        return list(dict.fromkeys(concepts))

    @staticmethod
    def _build_concept_items(
        message: str,
        concepts: list[str],
        hits: list[KnowledgeHit],
        mistake: Mistake | None,
        previous_items: list[dict[str, Any]] | None = None,
        assessed: bool = False,
    ) -> list[dict[str, Any]]:
        """Keep the concept trace explainable without changing legacy labels."""
        explicit = set(extract_explicit_concepts(message))
        hits_by_label = {
            hit.item.concept_zh: hit.item
            for hit in hits
            if hit.item.concept_zh
        }
        previous_by_label = {
            str(item.get("label")): item
            for item in (previous_items or [])
            if item.get("label")
        }
        hit_ids_by_label = {
            hit.item.concept_zh: hit.item.id
            for hit in hits
            if hit.item.concept_zh
        }
        result: list[dict[str, Any]] = []

        for index, label in enumerate(concepts):
            knowledge_item = hits_by_label.get(label) or next(
                (
                    hit.item
                    for hit in hits
                    if hit.item.concept_zh
                    and (
                        label in hit.item.concept_zh
                        or hit.item.concept_zh in label
                    )
                ),
                None,
            )
            previous = previous_by_label.get(label, {})
            is_mistake = bool(mistake and mistake.concept == label)

            if is_mistake:
                source = "mistake"
                evidence = f"步骤检查定位到：{mistake.label}"
            elif label in explicit:
                source = "explicit"
                evidence = "题目或提问中直接提及"
            elif knowledge_item:
                source = "retrieval"
                evidence = "根据题意与本地知识库匹配"
            elif previous:
                source = "conversation"
                evidence = "沿用本会话上一轮的考点"
            else:
                source = "rule"
                evidence = "根据题目中的数学符号与规则识别"

            chapter = (
                knowledge_item.chapter
                if knowledge_item
                else str(previous.get("chapter") or "")
            )
            section = (
                knowledge_item.section
                if knowledge_item
                else str(previous.get("section") or "")
            )
            description = (
                knowledge_item.description
                if knowledge_item
                else str(previous.get("description") or "")
            )
            description = " ".join(description.split())
            if len(description) > 180:
                description = f"{description[:177]}..."

            raw_prerequisites = (
                knowledge_item.prerequisite
                if knowledge_item
                else previous.get("prerequisites") or []
            )
            prerequisites: list[dict[str, str]] = []
            for prerequisite in raw_prerequisites:
                if isinstance(prerequisite, dict):
                    prerequisite_label = str(
                        prerequisite.get("label")
                        or prerequisite.get("display_name")
                        or prerequisite.get("id")
                        or ""
                    )
                    prerequisite_id = str(
                        prerequisite.get("id")
                        or prerequisite.get("unit_id")
                        or hit_ids_by_label.get(prerequisite_label)
                        or f"concept:{prerequisite_label}"
                    )
                else:
                    prerequisite_label = str(prerequisite)
                    prerequisite_id = str(
                        hit_ids_by_label.get(prerequisite_label)
                        or f"concept:{prerequisite_label}"
                    )
                if prerequisite_label:
                    prerequisites.append(
                        {"id": prerequisite_id, "label": prerequisite_label}
                    )

            result.append(
                {
                    "id": (
                        knowledge_item.id
                        if knowledge_item
                        else str(previous.get("id") or f"concept:{label}")
                    ),
                    "label": label,
                    "subject": (
                        knowledge_item.subject
                        if knowledge_item
                        else str(previous.get("subject") or "")
                    ),
                    "chapter": chapter,
                    "section": section,
                    "path": [part for part in (chapter, section) if part],
                    "description": description,
                    "role": "primary" if index == 0 else "related",
                    "assessed": bool(index == 0 and assessed),
                    "source": source,
                    "evidence": evidence,
                    "prerequisites": prerequisites,
                }
            )

        return result

    def _finalize_learning_state(
        self,
        state: dict[str, Any],
        concepts: list[str],
        verifier_result: VerifyResult,
        mistake: Mistake | None,
    ) -> dict[str, float | int | str]:
        mastery_score = self.settings.initial_mastery
        mastery_delta = 0.0
        hint_level = 0

        if mistake:
            try:
                self.repository.add_mistake_event(
                    user_id=state["user_id"],
                    session_id=state["session_id"],
                    subject=state.get("detected_subject") or state["subject"],
                    concept=mistake.concept,
                    mistake_code=mistake.code,
                )
            except Exception:
                logger.exception("Mistake event persistence failed")

        if concepts:
            primary_concept = concepts[0]
            existing = self.repository.get_mastery(
                state["user_id"],
                primary_concept,
            )
            mastery_score = (
                existing["score"]
                if existing
                else self.settings.initial_mastery
            )

            if (
                verifier_result.verified
                and verifier_result.is_correct is not None
                and state.get("intent") is Intent.CHECK_STUDENT_STEP
            ):
                from app.memory.mastery import LearningEvent
                event = LearningEvent(
                    event_type="check_step",
                    correct=verifier_result.is_correct,
                    hint_level=1 if state.get("requested_hint") else 0,
                    difficulty=self.settings.default_difficulty,
                    error_type=mistake.code if mistake else None
                )
                update = update_mastery(
                    mastery_score,
                    event,
                    slip_probability=self.settings.bkt_slip_probability,
                    guess_probabilities=(
                        self.settings.bkt_guess_independent,
                        self.settings.bkt_guess_light_hint,
                        self.settings.bkt_guess_heavy_hint,
                    ),
                    learn_probabilities=(
                        self.settings.bkt_learn_independent,
                        self.settings.bkt_learn_light_hint,
                        self.settings.bkt_learn_heavy_hint,
                    ),
                )
                mastery_delta = update.delta
                mastery_score = update.new_score
                self.repository.upsert_mastery(
                    state["user_id"],
                    primary_concept,
                    mastery_score,
                    verifier_result.is_correct,
                )

            consecutive_errors = self.repository.get_consecutive_errors(
                state["user_id"],
                primary_concept,
            )
            hint_level = decide_hint_level(
                mastery_score,
                consecutive_errors,
                state.get("requested_hint", False),
                state.get("mode", "socratic"),
                error_thresholds=(
                    self.settings.hint_error_light,
                    self.settings.hint_error_formula,
                    self.settings.hint_error_near_answer,
                ),
                mastery_thresholds=(
                    self.settings.hint_mastery_formula,
                    self.settings.hint_mastery_light,
                ),
            ).value

            # --- KNOWLEDGE GRAPH LINKAGE ---
            if (
                consecutive_errors
                >= self.settings.remediation_error_threshold
                or mastery_score
                < self.settings.remediation_mastery_threshold
            ):
                primary_item = next(
                    (
                        hit.item
                        for hit in state.get("hits", [])
                        if hit.item.id == primary_concept
                        or hit.item.concept_zh == primary_concept
                    ),
                    state.get("hits", [None])[0].item
                    if state.get("hits")
                    else None,
                )
                if primary_item and primary_item.prerequisite:
                    from app.knowledge.search import get_knowledge_by_refs

                    prereq_items = get_knowledge_by_refs(
                        primary_item.prerequisite,
                        subject=primary_item.subject,
                    )
                    if prereq_items:
                        state["prerequisite_hints"] = [
                            {"id": p.id, "name": p.concept_zh, "desc": p.description}
                            for p in prereq_items
                        ]
            # -------------------------------

        try:
            self.repository.add_attempt(
                session_id=state["session_id"],
                user_id=state["user_id"],
                problem_text=state["message"],
                student_step=(
                    state["message"]
                    if state.get("intent") is Intent.CHECK_STUDENT_STEP
                    else None
                ),
                is_correct=(
                    verifier_result.is_correct
                    if verifier_result.verified
                    else None
                ),
                mistake_code=mistake.code if mistake else None,
                verifier_summary=verifier_result.summary,
            )
        except Exception:
            logger.exception("Attempt persistence failed")

        return {
            "mastery_score": mastery_score,
            "mastery_delta": mastery_delta,
            "mastery_label_str": mastery_label(mastery_score),
            "hint_level": hint_level,
            "prerequisite_hints": state.get("prerequisite_hints", []),
        }
