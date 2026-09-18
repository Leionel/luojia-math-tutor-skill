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
from app.agents.code_executor import execute_python_code
from app.agents.multimodal import normalize_image_reference
from app.agents.vision_agent import VisionParser
from app.knowledge.search import search_knowledge_semantic
from app.llm.openai_compatible import OpenAICompatibleClient
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.tutor.fast_context import FastContextCollector
from app.tutor.fast_path import (
    VerificationMode,
    learning_objective_for_intent,
    route_fast_path,
)
from app.tutor.intent_router import Intent
from app.tutor.policy_router import PolicyRouter
from app.tutor.prompt_builder import (
    HintLevel,
    build_examiner_prompt,
    build_messages,
    build_teacher_prompt,
    build_verifier_prompt,
)

logger = logging.getLogger(__name__)


def sse(event: str, data: dict) -> str:
    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


class AgentState(TypedDict, total=False):
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
    if state.get("requires_policy_fallback"):
        return "policy_fallback"
    if state.get("intent") == Intent.PROOF_HINT:
        return "proof_tutor"
    if state.get("pedagogical_action") == "generate_exercise":
        return "examiner"
    if _needs_llm_verifier(state):
        return "verifier"
    return "teacher"


def route_after_policy(state: AgentState) -> str:
    if state.get("intent") == Intent.PROOF_HINT:
        return "proof_tutor"
    if state.get("pedagogical_action") == "generate_exercise":
        return "examiner"
    if _needs_llm_verifier(state):
        return "verifier"
    return "teacher"


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
        self.skill_text = settings.skill_file.read_text(encoding="utf-8")
        self.workflow = self.build_tutor_graph()

    def build_tutor_graph(self) -> CompiledGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node("vision_parse", self.vision_parse_node)
        workflow.add_node("fast_context", self.fast_context_node)
        workflow.add_node("policy_fallback", self.policy_fallback_node)
        workflow.add_node("verifier", self.verifier_node)
        workflow.add_node("teacher", self.teacher_node)
        workflow.add_node("examiner", self.examiner_node)
        workflow.add_node("proof_tutor", self.proof_tutor_node)

        workflow.add_edge(START, "vision_parse")
        workflow.add_edge("vision_parse", "fast_context")
        workflow.add_conditional_edges(
            "fast_context",
            route_after_context,
            {
                "policy_fallback": "policy_fallback",
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
                "verifier": "verifier",
                "teacher": "teacher",
                "examiner": "examiner",
                "proof_tutor": "proof_tutor",
            },
        )
        workflow.add_edge("verifier", "teacher")
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
                f"{parsed_text}"
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
            return {
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
            return {
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
                    f"已参考用户绑定文档（{len(context.document_chunks)} 个片段）"
                )
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
        decision = await self.policy_router.decide_route(
            state["message"],
            state["intent"],
            state.get("user_api_key"),
            state.get("model"),
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
        decided_state = {
            **state,
            "intent": decision.intent,
            "learning_objective": learning_objective_for_intent(decision.intent),
            "pedagogical_action": action.value,
            "requires_policy_fallback": False,
        }
        messages = self._build_base_messages(
            decided_state,
            self._history_from_messages(
                state.get("messages", []),
                state["message"],
            ),
            state.get("hits", []),
            state.get("document_chunks", []),
            state["verifier_result"],
            state.get("mistake"),
            state.get("mastery_score", 0.5),
            state.get("hint_level", 0),
            action.value,
            evidence_pack=state.get("evidence_pack"),
        )
        return {
            "intent": decision.intent,
            "pedagogical_action": action.value,
            "learning_objective": decided_state["learning_objective"],
            "requires_policy_fallback": False,
            "messages": messages,
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
            or bool(state.get("verification_result"))
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
        tool_evidence: list[dict[str, str]] = []
        verification_forced = False

        if on_progress:
            output_text = {
                "examiner": "已进入 Examiner 出题/测验阶段。",
                "proof_tutor": "已进入证明结构辅导阶段。",
                "teacher": "已进入 Teacher 启发式讲解阶段。",
            }.get(default_route, "已进入教学回答阶段。")
            await on_progress(f"[OUTPUT]\n{output_text}")

        try:
            max_rounds = max(0, min(self.settings.tool_max_rounds, 2))
            for tool_round in range(max_rounds + 1):
                candidate = await self._collect_model_response(
                    prompt,
                    state.get("user_api_key"),
                    state.get("model"),
                )
                metrics["llm_call_count"] = (
                    int(metrics.get("llm_call_count", 0)) + 1
                )
                code_blocks = self._extract_verify_code(candidate)
                if (
                    require_verification
                    and not code_blocks
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
                            "role": "user",
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
                for code in code_blocks:
                    result = await execute_python_code(
                        code,
                        timeout=self.settings.tool_timeout_seconds,
                    )
                    results.append(result)
                    tool_evidence.append({"code": code, "result": result})
                prompt = [
                    *prompt,
                    {"role": "assistant", "content": candidate},
                    {
                        "role": "user",
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
            upstream_failure = (state.get("verification_result") or {}).get("verified") is False
            if require_verification and not tool_evidence:
                response_text = (
                    "⚠️ 本轮未能完成符号验算，以下内容未经确定性验证，请仔细核对。\n\n"
                    + response_text
                )
                metrics["verification_enforced"] = "degraded"
            elif require_verification:
                metrics["verification_enforced"] = "enforced"
            else:
                metrics["verification_enforced"] = "not_required"
            if upstream_failure:
                failure_summary = (
                    state.get("verification_result") or {}
                ).get("summary") or "验证器未能确认本步推导。"
                response_text = f"❗ {failure_summary}\n\n{response_text}"

            metrics["sandbox_tool_calls"] = len(tool_evidence)
            metrics["teacher_first_token_ms"] = round(
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
            "metrics": metrics,
        }

    async def _collect_model_response(
        self,
        prompt: list[dict[str, Any]],
        api_key: str | None,
        model: str | None,
    ) -> str:
        response = ""
        async for token in self.llm.stream(
            prompt,
            api_key=api_key,
            model=model,
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
            parsed = json.loads(response_text[start:end])
            if isinstance(parsed, dict):
                is_correct = parsed.get("is_correct")
                if is_correct not in {True, False, None}:
                    is_correct = None
                reason = str(parsed.get("reason") or "").strip()
                summary = str(parsed.get("summary") or reason).strip()
                return {
                    "verified": bool(parsed.get("verified")),
                    "is_correct": is_correct,
                    "error_step": parsed.get("error_step"),
                    "reason": reason,
                    "summary": summary,
                }
        except (ValueError, json.JSONDecodeError):
            pass
        return {
            "verified": False,
            "is_correct": None,
            "error_step": None,
            "reason": "Verifier did not return the required JSON schema.",
            "summary": response_text.strip(),
        }

    @staticmethod
    def _callback(
        config: RunnableConfig | None,
        name: str,
    ) -> Any | None:
        if not config:
            return None
        return config.get("configurable", {}).get(name)
