import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.knowledge.schema import KnowledgeHit
from app.knowledge.search import search_knowledge_local
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
    Awaitable[list[KnowledgeHit]],
]


@dataclass
class FastContext:
    history: list[dict[str, str]]
    hits: list[KnowledgeHit]
    document_chunks: list[str]
    concepts: list[str]
    verifier_result: VerifyResult
    mistake: Mistake | None
    mastery_score: float
    mastery_delta: float
    mastery_label_str: str
    hint_level: int
    metrics: dict[str, float | int | str | bool]


class FastContextCollector:
    def __init__(
        self,
        repository: Repository,
        timeout_seconds: float = 0.35,
        local_search: LocalSearch = search_knowledge_local,
    ):
        self.repository = repository
        self.timeout_seconds = timeout_seconds
        self.local_search = local_search

    async def collect(self, state: dict[str, Any]) -> FastContext:
        started = time.perf_counter()
        history, document_id = await asyncio.to_thread(
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

        hits = results.get("hits", [])
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
        concepts = self._derive_concepts(state["message"], hits, mistake)
        mastery = await asyncio.to_thread(
            self._finalize_learning_state,
            state,
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
            hits=hits,
            document_chunks=document_chunks,
            concepts=concepts,
            verifier_result=verifier_result,
            mistake=mistake,
            mastery_score=mastery["mastery_score"],
            mastery_delta=mastery["mastery_delta"],
            mastery_label_str=mastery["mastery_label_str"],
            hint_level=mastery["hint_level"],
            metrics=metrics,
        )

    def _prepare_session(
        self,
        user_id: str,
        session_id: str,
        message: str,
    ) -> tuple[list[dict[str, str]], str | None]:
        self.repository.ensure_user(user_id)
        db_messages = self.repository.list_messages(session_id)
        history = [
            {"role": item["role"], "content": item["content"]}
            for item in db_messages
        ]
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
        return history, document_id

    async def _collect_local_hits(
        self,
        state: dict[str, Any],
    ) -> tuple[list[KnowledgeHit], float]:
        started = time.perf_counter()
        try:
            hits = await self.local_search(
                state["message"],
                state.get("detected_subject") or state.get("subject"),
                5,
            )
        except Exception:
            logger.exception("Local knowledge search failed")
            hits = []
        return hits, (time.perf_counter() - started) * 1000

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
    def _derive_concepts(
        message: str,
        hits: list[KnowledgeHit],
        mistake: Mistake | None,
    ) -> list[str]:
        concepts = [
            hit.item.concept_zh
            for hit in hits[:3]
            if hit.item.concept_zh
        ]
        if ("∫" in message or "\\int" in message) and "幂函数积分" not in concepts:
            concepts.insert(0, "幂函数积分")
        if mistake and mistake.concept not in concepts:
            concepts.insert(0, mistake.concept)
        return list(dict.fromkeys(concepts))

    def _finalize_learning_state(
        self,
        state: dict[str, Any],
        concepts: list[str],
        verifier_result: VerifyResult,
        mistake: Mistake | None,
    ) -> dict[str, float | int | str]:
        mastery_score = 0.5
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
            mastery_score = existing["score"] if existing else 0.5

            if (
                verifier_result.verified
                and verifier_result.is_correct is not None
                and state.get("intent") is Intent.CHECK_STUDENT_STEP
            ):
                update = update_mastery(
                    mastery_score,
                    verifier_result.is_correct,
                    1 if state.get("requested_hint") else 0,
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
            ).value

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
        }
