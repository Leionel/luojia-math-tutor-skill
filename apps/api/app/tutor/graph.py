import json
import logging
import asyncio
import re
import time
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph as CompiledGraph

from app.config import Settings
from app.agents.code_executor import execute_python_result
from app.agents.multimodal import normalize_image_reference
from app.agents.vision_agent import VisionParser
from app.knowledge.search import search_knowledge_semantic
from app.llm.openai_compatible import OpenAICompatibleClient
from app.llm.completion_protocol import ModelCompletionError
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.tutor.fast_context import FastContextCollector
from app.search.web_search import search_status_text
from app.tutor.fast_path import (
    VerificationMode,
    learning_objective_for_intent,
    route_fast_path,
    verification_mode_for,
)
from app.tutor.intent_router import Intent
from app.tutor.policy_router import PolicyRouter
from app.tutor.prompt_policy import load_teaching_prompt
from app.tutor.answer_guard import (
    AnswerDeliveryError, answer_requested, check_delivery, check_root_contract, guard_report,
)
from pydantic import BaseModel, ConfigDict, StrictBool, ValidationError
from app.tutor.prompt_builder import (
    HintLevel,
    build_examiner_prompt,
    build_messages,
    build_teacher_prompt,
    build_verifier_prompt,
)

logger = logging.getLogger(__name__)


class VerificationReview(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    verified: StrictBool
    is_correct: StrictBool | None
    error_step: str | None
    reason: str
    summary: str


def sse(event: str, data: dict) -> str:
    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


class AgentState(TypedDict, total=False):
    learning_context: dict[str, Any]
    root_submission: dict[str, Any]
    root_diagnosis: dict[str, Any]
    web_search_report: dict[str, Any]
    web_search_reason: str
    external_fact_question: bool
    web_search: bool
    reasoning_effort: str
    awaiting_vision_confirmation: bool
    awaiting_intent_clarification: bool
    tool_evidence: list[dict[str, Any]]
    answer_guard: dict[str, Any]
    message: str
    session_id: str
    user_id: str
    subject: str
    mode: str
    user_api_key: str | None
    model: str | None
    requested_hint: bool
    image_urls: list[str] | None
    original_message: str
    vision_result: dict[str, Any]

    intent: Intent
    pedagogical_action: str
    verification_mode: str
    confidence: float
    requires_policy_fallback: bool
    verification_result: dict[str, Any]
    detected_subject: str
    hits: list[Any]
    document_chunks: list[str]
    verifier_result: VerifyResult
    mistake: Any | None
    concepts: list[str]
    concept_items: list[dict[str, Any]]
    mastery_score: float
    mastery_delta: float
    mastery_label_str: str
    hint_level: int
    learning_objective: str

    messages: list[dict[str, Any]]
    thinking_steps: list[str]
    final_output: str
    thinking_chain: str
    evidence_pack: Any
    metrics: dict[str, float | int | str | bool]


def _needs_llm_verifier(state: AgentState) -> bool:
    verification_mode = state.get("verification_mode")
    if verification_mode == VerificationMode.LLM.value:
        return True
    if verification_mode == VerificationMode.SYMBOLIC.value:
        result = state.get("verifier_result")
        return not result or not result.verified
    return False


def route_after_context(state: AgentState) -> str:
    if state.get("intent") == Intent.PROOF_HINT:
        return "verifier"
    if state.get("pedagogical_action") == "generate_exercise":
        return "examiner"
    if _needs_llm_verifier(state):
        return "verifier"
    return "teacher"


def route_after_policy(state: AgentState) -> str:
    return "stop" if state.get("awaiting_intent_clarification") else "fast_context"


class TutorWorkflow:
    def __init__(self, settings: Settings, repository: Repository):
        self.settings = settings
        self.repository = repository
        self.llm = OpenAICompatibleClient(settings)
        self.vision_parser = VisionParser(settings, self.llm)
        self.policy_router = PolicyRouter(self.llm)
        self.context_collector = FastContextCollector(repository, settings=settings)
        self._semantic_worker_task: asyncio.Task | None = None
        self._semantic_worker_stop = asyncio.Event()
        self.skill_text = load_teaching_prompt(settings.skill_file)
        self.workflow = self.build_tutor_graph()

    async def root_diagnostic_node(self, state: AgentState, config: RunnableConfig) -> dict:
        from app.knowledge.course_service import get_course_service
        from app.tutor.root_diagnostics import RootEpisodeService, RootSubmission, feedback_text
        service = RootEpisodeService(get_course_service("numerical_analysis"))
        submission = RootSubmission.model_validate(state["root_submission"])
        work = asyncio.create_task(asyncio.to_thread(service.submit, state["user_id"], state["session_id"], submission, mode=state.get("mode", "socratic"), model=state.get("model")))
        try:
            report = await asyncio.shield(work)
        except asyncio.CancelledError:
            # A Python worker cannot be killed halfway through its transaction.
            # Finish its bounded write and retain an unknown delivery outcome.
            try:
                report = await work
                await asyncio.to_thread(service.delivery_interrupted, state["user_id"], state["session_id"], report["episode_id"], submission.attempt_id)
            except Exception:
                logger.exception("Could not record interrupted root delivery")
            raise
        await asyncio.to_thread(self.repository.ensure_user, state["user_id"])
        await asyncio.to_thread(self.repository.add_message, state["session_id"], "user", state["message"])
        try:
            output = feedback_text(report)
            delivery = check_root_contract(report, output)
        except Exception:
            await asyncio.to_thread(service.delivery_interrupted, state["user_id"], state["session_id"], report["episode_id"], submission.attempt_id)
            raise
        on_token = self._callback(config, "on_token")
        if on_token:
            await on_token(sse("message", {"content": output}))
        return {"root_diagnosis": report, "final_output": output, "answer_guard": delivery, "intent": Intent.CHECK_STUDENT_STEP,
                "pedagogical_action": report["action"], "verification_mode": "none",
                "requires_policy_fallback": False, "concepts": report["unit_ids"],
                "hint_level": report["help_level"], "metrics": {**state.get("metrics", {}), "route": "root_diagnostic"}}

    def _traced_node(self, node, phase):
        async def traced(state, config):
            if phase == "vision" and not state.get("image_urls"):
                return await node(state,config)
            callback = self._callback(config,"on_run_event")
            started = time.perf_counter()
            if callback:
                await callback(phase,"started")
            try:
                result = await node(state,config)
            except asyncio.CancelledError:
                if callback:
                    await callback(phase,"cancelled",duration_ms=(time.perf_counter()-started)*1000)
                raise
            except Exception as exc:
                if callback:
                    await callback(phase,"failed",duration_ms=(time.perf_counter()-started)*1000,
                                   error_code=exc.code if isinstance(exc,(ModelCompletionError,AnswerDeliveryError)) else "workflow_failed")
                raise
            if callback:
                status = "clarification" if result.get("awaiting_intent_clarification") or result.get("awaiting_vision_confirmation") else "succeeded"
                if phase == "review" and (result.get("verification_result") or {}).get("verified") is False:
                    status = "degraded"
                await callback(phase,status,duration_ms=(time.perf_counter()-started)*1000)
            return result
        return traced

    def build_tutor_graph(self) -> CompiledGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node("root_diagnostic", self._traced_node(self.root_diagnostic_node,"review"))
        workflow.add_node("vision_parse", self._traced_node(self.vision_parse_node,"vision"))
        workflow.add_node("fast_context", self._traced_node(self.fast_context_node,"context"))
        workflow.add_node("policy_fallback", self._traced_node(self.policy_fallback_node,"routing"))
        workflow.add_node("verifier", self._traced_node(self.verifier_node,"review"))
        workflow.add_node("teacher", self._traced_node(self.teacher_node,"generation"))
        workflow.add_node("examiner", self._traced_node(self.examiner_node,"generation"))
        workflow.add_node("proof_tutor", self._traced_node(self.proof_tutor_node,"generation"))

        workflow.add_conditional_edges(START, lambda state: "root" if state.get("root_submission") else "normal", {"root": "root_diagnostic", "normal": "vision_parse"})
        workflow.add_edge("root_diagnostic", END)
        workflow.add_conditional_edges(
            "vision_parse",
            lambda state: "stop" if state.get("awaiting_vision_confirmation") else "policy" if state.get("requires_policy_fallback") else "continue",
            {"stop": END, "policy": "policy_fallback", "continue": "fast_context"},
        )
        workflow.add_conditional_edges(
            "fast_context",
            route_after_context,
            {
                "verifier": "verifier",
                "teacher": "teacher",
                "examiner": "examiner",
                "proof_tutor": "proof_tutor",
            },
        )
        workflow.add_conditional_edges(
            "policy_fallback",
            route_after_policy,
            {
                "stop": END,
                "fast_context": "fast_context",
            },
        )
        workflow.add_conditional_edges(
            "verifier", lambda state: "proof" if state.get("intent") == Intent.PROOF_HINT else "teach",
            {"proof": "proof_tutor", "teach": "teacher"},
        )
        workflow.add_edge("teacher", END)
        workflow.add_edge("examiner", END)
        workflow.add_edge("proof_tutor", END)
        # SQLite history is the sole cross-turn authority. A process-local
        # checkpointer would diverge after a restart or under multiple workers.
        return workflow.compile()

    async def vision_parse_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict[str, Any]:
        references = state.get("image_urls") or []
        if not references:
            return {"vision_result": {}}

        started = time.perf_counter()
        try:
            normalized = await asyncio.gather(
                *(
                    asyncio.to_thread(
                        normalize_image_reference,
                        reference,
                        self.settings.upload_root,
                    )
                    for reference in references[:4]
                )
            )
            parsed = await self.vision_parser.parse_images(
                normalized,
                state.get("message", ""),
                api_key=state.get("user_api_key"),
            )
            problem_text = str(parsed.get("problem_text") or "").strip()
            latex = [str(item) for item in parsed.get("latex", [])]
            if not problem_text and not latex:
                raise ValueError("视觉模型没有返回可确认的题意。")
            parsed_text = "\n".join(
                part
                for part in (
                    problem_text,
                    "\n".join(f"$${item}$$" for item in latex),
                )
                if part
            )
            original = state.get("message", "").strip()
            enriched_message = (
                f"{original}\n\n[图片解析草稿，待学生确认]\n{parsed_text}"
                if original
                else f"[图片解析草稿，待学生确认]\n{parsed_text}"
            )
            route = route_fast_path(
                enriched_message,
                state.get("mode", "socratic"),
                state.get("subject", "auto"),
            )
            confirmation = (
                "我先把图片识别为下面这道题，请你确认公式和条件是否准确；"
                "若有误请直接指出：\n\n"
                f"{parsed_text}\n\n请确认后继续，或先修正识别有误的条件。"
            )
            on_thinking = self._callback(config, "on_thinking")
            if on_thinking:
                await on_thinking(
                    sse(
                        "vision_confirmation",
                        {
                            "content": confirmation,
                            "parsed": parsed,
                            "requires_confirmation": True,
                        },
                    )
                )
            on_token = self._callback(config, "on_token")
            if on_token:
                await on_token(sse("message", {"content": confirmation}))
            return {
                "awaiting_vision_confirmation": True,
                "final_output": confirmation,
                "original_message": state.get("message", ""),
                "message": enriched_message,
                "vision_result": parsed,
                "intent": route.intent,
                "detected_subject": route.subject,
                "pedagogical_action": route.pedagogical_action,
                "learning_objective": route.learning_objective,
                "verification_mode": route.verification_mode.value,
                "confidence": route.confidence,
                "requires_policy_fallback": route.requires_policy_fallback,
                "metrics": {
                    **state.get("metrics", {}),
                    "vision_parse_ms": round(
                        (time.perf_counter() - started) * 1000,
                        2,
                    ),
                },
            }
        except Exception as exc:
            logger.warning("Vision parsing rejected: %s", exc)
            on_progress = self._callback(config, "on_progress")
            if on_progress:
                await on_progress(f"[VISION]\n图片解析未完成：{exc}")
            failure = "图片识别未完成，请重新上传清晰图片或输入题目文字；本轮没有开始解题。"
            on_token = self._callback(config, "on_token")
            if on_token:
                await on_token(sse("message", {"content": failure}))
            return {
                "awaiting_vision_confirmation": True,
                "final_output": failure,
                "vision_result": {"error": str(exc)},
                "metrics": {
                    **state.get("metrics", {}),
                    "vision_parse_ms": round(
                        (time.perf_counter() - started) * 1000,
                        2,
                    ),
                },
            }

    async def fast_context_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict:
        context = await self.context_collector.collect(state)
        hits = []
        if not state.get("external_fact_question"):
            hits = self._merge_hits(
                context.hits,
                await asyncio.to_thread(
                    self.repository.get_semantic_cache,
                    str(state.get("detected_subject") or state.get("subject") or "auto"),
                    state["message"],
                    self.settings.semantic_cache_ttl_seconds,
                ),
            )
        state_with_context = {
            **state,
            "prerequisite_hints": context.prerequisite_hints,
            "web_search_report": context.web_search_report,
        }
        messages = self._build_base_messages(
            state_with_context,
            context.history,
            hits,
            context.document_chunks,
            context.verifier_result,
            context.mistake,
            context.mastery_score,
            context.hint_level,
            state["pedagogical_action"],
            evidence_pack=context.evidence_pack,
        )
        metrics = {
            **state.get("metrics", {}),
            **context.metrics,
        }
        branch_state: AgentState = {
            **state_with_context,
            "verifier_result": context.verifier_result,
            "pedagogical_action": state["pedagogical_action"],
        }
        branch = route_after_context(branch_state)
        metrics["route"] = {
            "teacher": "teacher",
            "examiner": "examiner",
            "verifier": "verifier_teacher",
            "proof_tutor": "proof_tutor",
            "policy_fallback": "policy_fallback",
        }[branch]

        on_thinking = self._callback(config, "on_thinking")
        if on_thinking:
            await on_thinking(
                sse(
                    "meta",
                    {
                        "intent": state["intent"].value,
                        "subject": state["detected_subject"],
                        "concepts": context.concepts,
                        "concept_items": context.concept_items,
                        "verified": context.verifier_result.verified,
                        "is_correct": context.verifier_result.is_correct,
                        "mistake": (
                            context.mistake.label
                            if context.mistake
                            else None
                        ),
                        "verifier_summary": context.verifier_result.summary,
                        "hint_level": context.hint_level,
                        "mastery_score": context.mastery_score,
                        "mastery_label": context.mastery_label_str,
                        "mastery_delta": context.mastery_delta,
                        "learning_objective": state[
                            "learning_objective"
                        ],
                        "pedagogical_action": state[
                            "pedagogical_action"
                        ],
                        "route": metrics["route"],
                        "fast_context_ms": metrics["fast_context_ms"],
                        "web_search": context.web_search_report,
                    },
                )
            )

        on_progress = self._callback(config, "on_progress")
        if on_progress:
            rag_items = []
            if context.hits:
                rag_items.append(
                    f"已检索本地知识库（{len(context.hits)} 条相关知识点）"
                )
            if context.concepts:
                rag_items.append(
                    f"已定位相关概念：{'、'.join(context.concepts[:3])}"
                )
            rag_items.append("已载入会话历史与当前掌握度评估")
            if context.document_chunks:
                rag_items.append(
                    f"已参考文档与外部资料（{len(context.document_chunks)} 个片段）"
                )
            rag_items.append(search_status_text(context.web_search_report))
            await on_progress(f"[隐式 RAG]\n{'；'.join(rag_items)}。")

            verifier_result = context.verifier_result
            if verifier_result.verified and verifier_result.is_correct is True:
                verify_text = "SymPy 符号验证已通过。"
            elif verifier_result.verified and verifier_result.is_correct is False:
                verify_text = (
                    verifier_result.summary
                    or "SymPy 符号验证发现当前步骤与标准结果不一致。"
                )
            else:
                verify_text = "本轮未触发符号校验。"
            await on_progress(f"[VERIFY]\n{verify_text}")

        return {
            "pedagogical_action": state["pedagogical_action"],
            "learning_objective": state["learning_objective"],
            "hits": hits,
            "document_chunks": context.document_chunks,
            "web_search_report": context.web_search_report,
            "concepts": context.concepts,
            "concept_items": context.concept_items,
            "verifier_result": context.verifier_result,
            "mistake": context.mistake,
            "mastery_score": context.mastery_score,
            "mastery_delta": context.mastery_delta,
            "mastery_label_str": context.mastery_label_str,
            "hint_level": context.hint_level,
            "evidence_pack": context.evidence_pack,
            "messages": messages,
            "metrics": metrics,
        }

    def schedule_semantic_enrichment(
        self,
        message: str,
        subject: str,
        api_key: str | None,
    ) -> None:
        # User-supplied keys are intentionally never persisted in the durable
        # queue. Shared enrichment uses only the operator-managed service key.
        if not self.settings.llm_api_key:
            return
        self.repository.enqueue_semantic_job(subject, message)
        if self._semantic_worker_task is None or self._semantic_worker_task.done():
            self._semantic_worker_stop.clear()
            self._semantic_worker_task = asyncio.create_task(
                self._semantic_worker_loop()
            )

    async def start_background_worker(self) -> None:
        if not self.settings.llm_api_key:
            return
        await asyncio.to_thread(self.repository.recover_semantic_jobs)
        if self._semantic_worker_task is None or self._semantic_worker_task.done():
            self._semantic_worker_stop.clear()
            self._semantic_worker_task = asyncio.create_task(
                self._semantic_worker_loop()
            )

    async def stop_background_worker(self) -> None:
        self._semantic_worker_stop.set()
        task = self._semantic_worker_task
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        self._semantic_worker_task = None

    async def _semantic_worker_loop(self) -> None:
        while not self._semantic_worker_stop.is_set():
            worked = await self._run_next_semantic_job()
            if worked:
                continue
            try:
                await asyncio.wait_for(
                    self._semantic_worker_stop.wait(),
                    timeout=max(0.1, self.settings.semantic_worker_poll_seconds),
                )
            except TimeoutError:
                pass

    async def _run_next_semantic_job(self) -> bool:
        job = await asyncio.to_thread(self.repository.claim_semantic_job)
        if not job:
            return False
        try:
            hits = await search_knowledge_semantic(
                job["query"],
                job["subject"],
                limit=5,
                api_key=None,
            )
            await asyncio.to_thread(
                self.repository.complete_semantic_job,
                job["id"],
                job["subject"],
                job["query"],
                hits,
            )
        except Exception as exc:
            logger.exception("Durable semantic enrichment failed")
            await asyncio.to_thread(
                self.repository.fail_semantic_job,
                job["id"],
                str(exc),
            )
        return True

    async def _run_semantic_enrichment(
        self,
        message: str,
        subject: str,
        api_key: str | None,
    ) -> None:
        """Compatibility entry point; work is now claimed from SQLite."""
        self.schedule_semantic_enrichment(message, subject, api_key)
        await self._run_next_semantic_job()

    async def policy_fallback_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict:
        started = time.perf_counter()
        # Resolve intent before the context collector can write learning events.
        history = await asyncio.to_thread(self.repository.list_messages, state["session_id"])
        decision = await self.policy_router.decide_route(
            state["message"],
            state["intent"],
            state.get("user_api_key"),
            state.get("model"),
            history=[item for item in history if item.get("role") in {"user", "assistant"}],
        )
        action = decision.action
        metrics = dict(state.get("metrics", {}))
        metrics["llm_call_count"] = (
            int(metrics.get("llm_call_count", 0)) + 1
        )
        metrics["policy_fallback_ms"] = round(
            (time.perf_counter() - started) * 1000,
            2,
        )
        metrics["route"] = f"policy_{action.value}"
        metrics["policy_confidence"] = decision.confidence
        metrics["policy_uncertain"] = decision.uncertain
        if decision.uncertain:
            clarification = "你想让我讲解概念、检查当前步骤，还是出一道练习？请补充题目或你卡住的那一步，我再继续。"
            on_token = self._callback(config, "on_token")
            if on_token:
                await on_token(sse("message", {"content": clarification}))
            return {"awaiting_intent_clarification": True, "final_output": clarification,
                    "requires_policy_fallback": False, "confidence": decision.confidence,
                    "metrics": {**metrics, "route": "intent_clarification"}}
        return {
            "intent": decision.intent,
            "learning_objective": learning_objective_for_intent(decision.intent),
            "pedagogical_action": action.value,
            "verification_mode": verification_mode_for(state["message"], decision.intent).value,
            "confidence": decision.confidence,
            "requires_policy_fallback": False,
            "metrics": metrics,
        }

    async def verifier_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict:
        started = time.perf_counter()
        prompt = self._normalize_prompt(build_verifier_prompt(state))
        metrics = dict(state.get("metrics", {}))
        metrics["llm_call_count"] = (
            int(metrics.get("llm_call_count", 0)) + 1
        )
        metrics["route"] = "verifier_teacher"
        try:
            response_text = await self.llm.chat_completion(
                prompt,
                api_key=state.get("user_api_key"),
                model=state.get("model"),
            )
            verification_result = self._parse_verifier_response(
                response_text
            )
        except Exception as exc:
            logger.error("Verifier node failed: %s", exc, exc_info=True)
            verification_result = {
                "verified": False,
                "summary": (
                    "验证服务暂不可用，不应对当前推导作确定性判断。"
                ),
            }
        metrics["verifier_ms"] = round(
            (time.perf_counter() - started) * 1000,
            2,
        )
        return {
            "verification_result": verification_result,
            "metrics": metrics,
        }

    async def teacher_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict:
        # Hard gate: whether symbolic verification runs is decided by the
        # pipeline (verification mode / an upstream verifier verdict), never
        # by the model voluntarily emitting a [VERIFY] tag.
        require_verification = (
            state.get("verification_mode") == VerificationMode.SYMBOLIC.value
        )
        return await self._stream_generation(
            state,
            config,
            build_teacher_prompt(state),
            default_route="teacher",
            require_verification=require_verification,
        )

    async def examiner_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict:
        return await self._stream_generation(
            state,
            config,
            build_examiner_prompt(state),
            default_route="examiner",
        )

    async def proof_tutor_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict:
        from app.tutor.proof_tutor import build_proof_tutor_prompt

        state = {**state, "metrics": {**state.get("metrics", {}), "route": "proof_tutor"}}
        return await self._stream_generation(
            state,
            config,
            build_proof_tutor_prompt(state),
            default_route="proof_tutor",
        )

    async def _stream_generation(
        self,
        state: AgentState,
        config: RunnableConfig,
        messages: list,
        default_route: str,
        require_verification: bool = False,
    ) -> dict:
        prompt = self._normalize_prompt(messages)
        metrics = dict(state.get("metrics", {}))
        if not metrics.get("route") or metrics["route"] == "policy_fallback":
            metrics["route"] = default_route

        on_token = self._callback(config, "on_token")
        on_progress = self._callback(config, "on_progress")
        started = time.perf_counter()
        response_text = ""
        tool_evidence: list[dict[str, Any]] = []
        verification_forced = False

        if on_progress:
            output_text = {
                "examiner": "正在生成练习题。",
                "proof_tutor": "已进入证明结构辅导阶段。",
                "teacher": "正在组织讲解。",
            }.get(default_route, "已进入教学回答阶段。")
            await on_progress(f"[OUTPUT]\n{output_text}")

        try:
            max_rounds = 0 if state.get("learning_context") else max(0, min(self.settings.tool_max_rounds, 2))
            run_event = self._callback(config,"on_run_event")
            for tool_round in range(max_rounds + 1):
                if run_event:
                    await run_event("model","started",round=tool_round)
                candidate = await self._collect_model_response(
                    prompt,
                    state.get("user_api_key"),
                    state.get("model"),
                    effort=state.get("reasoning_effort", "medium"),
                    enable_search=False,
                )
                if run_event:
                    await run_event("model","succeeded",round=tool_round)
                metrics["llm_call_count"] = (
                    int(metrics.get("llm_call_count", 0)) + 1
                )
                code_blocks = self._extract_verify_code(candidate)
                if (
                    require_verification
                    and not code_blocks
                    and not tool_evidence
                    and not verification_forced
                    and tool_round < max_rounds
                ):
                    # The model skipped the mandatory verification pass. Force
                    # one explicit sandbox round instead of accepting the
                    # unverified answer silently.
                    verification_forced = True
                    prompt = [
                        *prompt,
                        {"role": "assistant", "content": candidate},
                        {
                            "role": "developer",
                            "content": (
                                "[系统强制要求] 本轮包含符号推导，必须先输出 [VERIFY] "
                                "后跟一个 python 代码块（仅允许 math/sympy），"
                                "对关键步骤执行 SymPy 验算；收到 [TOOL_RESULT] 后，"
                                "再把学生可见内容放在 [OUTPUT] 后。"
                            ),
                        },
                    ]
                    continue
                if not code_blocks or tool_round >= max_rounds:
                    response_text = self._visible_output(candidate)
                    break

                results = []
                for code in code_blocks[:1]:
                    if run_event:
                        await run_event("tool","started",round=tool_round)
                    result = await execute_python_result(
                        code,
                        timeout=self.settings.tool_timeout_seconds,
                    )
                    if run_event:
                        await run_event("tool","succeeded" if result.execution_succeeded else "degraded",round=tool_round,duration_ms=result.duration_ms,error_code=result.error_code)
                    record = {"code": code, "result": result.to_legacy_text(), **result.to_dict()}
                    results.append(record)
                    tool_evidence.append(record)
                prompt = [
                    *prompt,
                    {"role": "assistant", "content": candidate},
                    {
                        "role": "developer",
                        "content": (
                            "[TOOL_RESULT]\n"
                            + json.dumps(results, ensure_ascii=False)
                            + "\n[/TOOL_RESULT]\n"
                            "请根据真实执行结果纠正推导；如仍需验证可再请求一次，"
                            "最终学生可见内容必须放在 [OUTPUT] 后。"
                        ),
                    },
                ]

            # Observable verification outcome: a required-but-missing sandbox
            # run, or an upstream verifier failure, is surfaced to the student
            # instead of silently flowing into the final answer.
            if not response_text.strip():
                raise ModelCompletionError("model_empty_output")
            upstream_failure = (state.get("verification_result") or {}).get("verified") is False
            usable_tools = [item for item in tool_evidence if item["execution_succeeded"] and item["has_output"]]
            if run_event:
                await run_event("guard","started")
            try:
                response_text, delivery = await self._guard_answer(response_text, prompt, state,
                    any(item["execution_succeeded"] for item in tool_evidence), metrics)
            except AnswerDeliveryError:
                if run_event:
                    await run_event("guard","failed")
                raise
            if run_event:
                await run_event("guard","succeeded" if delivery["status"] in ("passed","repaired") else "degraded")
            if (require_verification and not usable_tools) or (tool_evidence and not usable_tools):
                response_text = (
                    "⚠️ 本轮未能完成符号验算，以下内容未经确定性验证，请仔细核对。\n\n"
                    + response_text
                )
                metrics["verification_enforced"] = "degraded"
            elif require_verification:
                metrics["verification_enforced"] = "enforced"
            else:
                metrics["verification_enforced"] = "not_required"
            if usable_tools:
                response_text = "计算工具已返回结果；这不等于下文全部结论已经得到数学验证，仍需核对条件与推导。\n\n" + response_text
                metrics["tool_validation_scope"] = "execution_only"
            if upstream_failure:
                failure_summary = (
                    state.get("verification_result") or {}
                ).get("summary") or "验证器未能确认本步推导。"
                response_text = f"❗ {failure_summary}\n\n{response_text}"

            metrics["sandbox_tool_calls"] = len(tool_evidence)
            metrics["sandbox_successful_calls"] = len(usable_tools)
            metrics["generation_buffer_ms"] = round(
                (time.perf_counter() - started) * 1000,
                2,
            )
            if on_token and response_text:
                await on_token(
                    sse(
                        "message",
                        {"type": "message", "content": response_text},
                    )
                )
        except Exception as exc:
            logger.error(
                "Generation node failed: %s",
                exc,
                exc_info=True,
            )
            raise

        return {
            "messages": [
                {"role": "assistant", "content": response_text}
            ],
            "final_output": response_text,
            "thinking_chain": "",
            "tool_evidence": tool_evidence,
            "answer_guard": delivery,
            "metrics": metrics,
        }

    async def _guard_answer(self, candidate: str, prompt: list, state: AgentState,
                            execution_succeeded: bool, metrics: dict) -> tuple[str, dict]:
        if not self.settings.answer_guard_enabled:
            return candidate, guard_report("unavailable", enabled=False)
        options = {"exercise": state.get("intent") == Intent.GENERATE_EXERCISE,
                   "allow_answer": answer_requested(state["message"]),
                   "execution_succeeded": execution_succeeded}
        try:
            verdict = check_delivery(candidate, **options)
        except Exception as exc:
            raise AnswerDeliveryError(guard_report("unavailable")) from exc
        if verdict.passed:
            return candidate, guard_report("passed")
        # This recovery path has no tool loop and cannot write learning events.
        repair_prompt = [*prompt, {"role": "assistant", "content": candidate}, {
            "role": "developer", "content": "只修复最后一条回答的交付违规，保留可支持的教学内容。"
            "只返回学生正文；不得调用工具或输出内部协议，不能把失败说成成功。"
            "没有执行学生的完整程序；工具执行不代表整个回答已证明。"
            + json.dumps({"rule_ids": verdict.violations, **options}, ensure_ascii=False)}]
        metrics["llm_call_count"] = int(metrics.get("llm_call_count", 0)) + 1
        metrics["guard_repair_calls"] = 1
        try:
            repaired = await self._collect_model_response(repair_prompt, state.get("user_api_key"),
                          state.get("model"), effort=state.get("reasoning_effort", "medium"))
            # Do not strip a repair tool request into an innocent-looking answer.
            second = check_delivery(repaired, **options)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            raise AnswerDeliveryError(guard_report("unavailable", verdict.violations, 1)) from exc
        if not second.passed:
            raise AnswerDeliveryError(guard_report("withheld", second.violations, 1))
        return repaired.strip(), guard_report("repaired", verdict.violations, 1)

    async def _collect_model_response(
        self,
        prompt: list[dict[str, Any]],
        api_key: str | None,
        model: str | None,
        effort: str = "medium",
        enable_search: bool = False,
    ) -> str:
        response = ""
        async for token in self.llm.stream(
            prompt,
            api_key=api_key,
            model=model,
            effort=effort,
            enable_search=enable_search,
        ):
            if isinstance(token, dict):
                if token.get("type") == "reasoning":
                    continue
                response += str(token.get("content", ""))
                continue
            content = str(token)
            if content.startswith("<think>"):
                continue
            response += content
        return response

    @staticmethod
    def _extract_verify_code(response: str) -> list[str]:
        blocks = re.findall(
            r"\[VERIFY\]\s*```(?:python|py)\s*\n(.*?)```",
            response,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return [block.strip() for block in blocks if block.strip()]

    @staticmethod
    def _visible_output(response: str) -> str:
        response = re.sub(r"\[VERIFY\]\s*```(?:python|py)\s*\n.*?```", "", response,
                          flags=re.IGNORECASE | re.DOTALL)
        output = re.search(
            r"\[OUTPUT\]\s*(.*)$",
            response,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if output:
            return output.group(1).strip()
        cleaned = re.sub(
            r"\[(?:PLAN|VERIFY|CORRECT)\].*?(?=\[(?:PLAN|VERIFY|CORRECT|OUTPUT)\]|$)",
            "",
            response,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return cleaned.strip()

    def _build_base_messages(
        self,
        state: AgentState,
        history: list[dict[str, str]],
        hits: list[Any],
        document_chunks: list[str],
        verifier_result: VerifyResult,
        mistake: Any | None,
        mastery_score: float,
        hint_level: int,
        pedagogical_action: str,
        evidence_pack: Any = None,
    ) -> list[dict[str, Any]]:
        return build_messages(
            skill_text=self.skill_text,
            user_message=state["message"],
            intent=state["intent"],
            subject=state["detected_subject"],
            hits=hits,
            verifier_result=verifier_result,
            mistake=mistake,
            mode=state["mode"],
            hint_level=HintLevel(hint_level),
            mastery_score=mastery_score,
            history=history,
            bilibili_results="",
            document_chunks=document_chunks,
            pedagogical_action=pedagogical_action,
            prerequisite_hints=state.get("prerequisite_hints"),
            evidence_pack=evidence_pack,
            web_search_report=state.get("web_search_report"),
            learning_context=state.get("learning_context"),
        )

    @staticmethod
    def _history_from_messages(
        messages: list[dict[str, Any]],
        current_message: str,
    ) -> list[dict[str, Any]]:
        history = [
            message
            for message in messages
            if message.get("role") in {"user", "assistant"}
        ]
        if (
            history
            and history[-1].get("role") == "user"
            and history[-1].get("content") == current_message
        ):
            history.pop()
        return history

    @staticmethod
    def _merge_hits(
        local_hits: list[Any],
        semantic_hits: list[Any],
    ) -> list[Any]:
        merged: list[Any] = []
        seen: set[str] = set()
        for hit in [*local_hits, *semantic_hits]:
            item_id = getattr(getattr(hit, "item", None), "id", None)
            key = item_id or repr(hit)
            if key in seen:
                continue
            seen.add(key)
            merged.append(hit)
        return merged[:5]

    @staticmethod
    def _normalize_prompt(messages: list | Any) -> list[dict[str, Any]]:
        if not isinstance(messages, list):
            return [{"role": "system", "content": str(messages)}]
        prompt: list[dict[str, Any]] = []
        for message in messages:
            if isinstance(message, dict):
                prompt.append(message)
                continue
            message_type = getattr(message, "type", "")
            role = {
                "system": "system",
                "human": "user",
                "ai": "assistant",
            }.get(message_type, "user")
            prompt.append(
                {
                    "role": role,
                    "content": str(getattr(message, "content", message)),
                }
            )
        return prompt

    @staticmethod
    def _parse_verifier_response(response_text: str) -> dict[str, Any]:
        try:
            start = response_text.index("{")
            end = response_text.rindex("}") + 1
            parsed = VerificationReview.model_validate_json(response_text[start:end])
            if not parsed.verified:
                parsed.is_correct = None
            return parsed.model_dump()
        except (ValueError, json.JSONDecodeError, ValidationError):
            pass
        return {
            "verified": False,
            "is_correct": None,
            "error_step": None,
            "reason": "Verifier did not return the required JSON schema.",
            "summary": "推理审查未返回有效状态，暂无法确认本步；请核对条件。",
        }

    @staticmethod
    def _callback(
        config: RunnableConfig | None,
        name: str,
    ) -> Any | None:
        if not config:
            return None
        return config.get("configurable", {}).get(name)
