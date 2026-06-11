import json
import logging
import asyncio
import time
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph as CompiledGraph

from app.config import Settings
from app.knowledge.search import search_knowledge_semantic
from app.llm.openai_compatible import OpenAICompatibleClient
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.tutor.fast_context import FastContextCollector
from app.tutor.fast_path import VerificationMode
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
    mastery_score: float
    mastery_delta: float
    mastery_label_str: str
    hint_level: int
    learning_objective: str

    messages: list[dict[str, str]]
    thinking_steps: list[str]
    final_output: str
    thinking_chain: str
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
    if state.get("pedagogical_action") == "generate_exercise":
        return "examiner"
    if _needs_llm_verifier(state):
        return "verifier"
    return "teacher"


def route_after_policy(state: AgentState) -> str:
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
        self.policy_router = PolicyRouter(self.llm)
        self.context_collector = FastContextCollector(repository)
        self._semantic_cache: dict[
            tuple[str, str],
            list[Any],
        ] = {}
        self._background_tasks: set[asyncio.Task] = set()
        self.skill_text = settings.skill_file.read_text(encoding="utf-8")
        self.workflow = self.build_tutor_graph()

    def build_tutor_graph(self) -> CompiledGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node("fast_context", self.fast_context_node)
        workflow.add_node("policy_fallback", self.policy_fallback_node)
        workflow.add_node("verifier", self.verifier_node)
        workflow.add_node("teacher", self.teacher_node)
        workflow.add_node("examiner", self.examiner_node)

        workflow.add_edge(START, "fast_context")
        workflow.add_conditional_edges(
            "fast_context",
            route_after_context,
            {
                "policy_fallback": "policy_fallback",
                "verifier": "verifier",
                "teacher": "teacher",
                "examiner": "examiner",
            },
        )
        workflow.add_conditional_edges(
            "policy_fallback",
            route_after_policy,
            {
                "verifier": "verifier",
                "teacher": "teacher",
                "examiner": "examiner",
            },
        )
        workflow.add_edge("verifier", "teacher")
        workflow.add_edge("teacher", END)
        workflow.add_edge("examiner", END)
        return workflow.compile(checkpointer=MemorySaver())

    async def fast_context_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict:
        context = await self.context_collector.collect(state)
        hits = self._merge_hits(
            context.hits,
            self._semantic_cache.get(
                (state["detected_subject"], state["message"]),
                [],
            ),
        )
        messages = self._build_base_messages(
            state,
            context.history,
            hits,
            context.document_chunks,
            context.verifier_result,
            context.mistake,
            context.mastery_score,
            context.hint_level,
            state["pedagogical_action"],
        )
        metrics = {
            **state.get("metrics", {}),
            **context.metrics,
        }
        branch_state: AgentState = {
            **state,
            "verifier_result": context.verifier_result,
            "pedagogical_action": state["pedagogical_action"],
        }
        branch = route_after_context(branch_state)
        metrics["route"] = {
            "teacher": "teacher",
            "examiner": "examiner",
            "verifier": "verifier_teacher",
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
            "verifier_result": context.verifier_result,
            "mistake": context.mistake,
            "mastery_score": context.mastery_score,
            "mastery_delta": context.mastery_delta,
            "mastery_label_str": context.mastery_label_str,
            "hint_level": context.hint_level,
            "messages": messages,
            "metrics": metrics,
        }

    def schedule_semantic_enrichment(
        self,
        message: str,
        subject: str,
        api_key: str | None,
    ) -> None:
        if not api_key and not self.settings.llm_api_key:
            return
        task = asyncio.create_task(
            self._run_semantic_enrichment(
                message,
                subject,
                api_key,
            )
        )
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _run_semantic_enrichment(
        self,
        message: str,
        subject: str,
        api_key: str | None,
    ) -> None:
        try:
            hits = await search_knowledge_semantic(
                message,
                subject,
                limit=5,
                api_key=api_key,
            )
        except Exception:
            logger.exception("Background semantic enrichment failed")
            return
        if len(self._semantic_cache) >= 128:
            oldest_key = next(iter(self._semantic_cache))
            self._semantic_cache.pop(oldest_key, None)
        self._semantic_cache[(subject, message)] = hits

    async def policy_fallback_node(
        self,
        state: AgentState,
        config: RunnableConfig,
    ) -> dict:
        started = time.perf_counter()
        action = await self.policy_router.decide_action(
            state["message"],
            state.get("user_api_key"),
            state.get("model"),
        )
        metrics = dict(state.get("metrics", {}))
        metrics["llm_call_count"] = (
            int(metrics.get("llm_call_count", 0)) + 1
        )
        metrics["policy_fallback_ms"] = round(
            (time.perf_counter() - started) * 1000,
            2,
        )
        metrics["route"] = f"policy_{action.value}"
        messages = self._build_base_messages(
            state,
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
        )
        return {
            "pedagogical_action": action.value,
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
        return await self._stream_generation(
            state,
            config,
            build_teacher_prompt(state),
            default_route="teacher",
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

    async def _stream_generation(
        self,
        state: AgentState,
        config: RunnableConfig,
        messages: list,
        default_route: str,
    ) -> dict:
        prompt = self._normalize_prompt(messages)
        metrics = dict(state.get("metrics", {}))
        metrics["llm_call_count"] = (
            int(metrics.get("llm_call_count", 0)) + 1
        )
        if not metrics.get("route") or metrics["route"] == "policy_fallback":
            metrics["route"] = default_route

        on_token = self._callback(config, "on_token")
        on_progress = self._callback(config, "on_progress")
        started = time.perf_counter()
        saw_content = False
        response_text = ""

        if on_progress:
            output_text = (
                "已进入 Examiner 出题/测验阶段。"
                if default_route == "examiner"
                else "已进入 Teacher 启发式讲解阶段。"
            )
            await on_progress(f"[OUTPUT]\n{output_text}")

        try:
            async for token in self.llm.stream(
                prompt,
                api_key=state.get("user_api_key"),
                model=state.get("model"),
            ):
                if isinstance(token, dict):
                    token_type = token.get("type")
                    content = str(token.get("content", ""))
                    is_reasoning = token_type == "reasoning"
                else:
                    content = str(token)
                    is_reasoning = content.startswith("<think>")
                    if is_reasoning:
                        content = content.replace(
                            "<think>",
                            "",
                        ).replace("</think>", "")

                if is_reasoning:
                    continue

                if not saw_content:
                    metrics["teacher_first_token_ms"] = round(
                        (time.perf_counter() - started) * 1000,
                        2,
                    )
                    saw_content = True
                response_text += content
                if on_token:
                    await on_token(
                        sse(
                            "message",
                            {
                                "type": "message",
                                "content": content,
                            },
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
            "metrics": metrics,
        }

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
    ) -> list[dict[str, str]]:
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
        )

    @staticmethod
    def _history_from_messages(
        messages: list[dict[str, str]],
        current_message: str,
    ) -> list[dict[str, str]]:
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
    def _normalize_prompt(messages: list | Any) -> list[dict[str, str]]:
        if not isinstance(messages, list):
            return [{"role": "system", "content": str(messages)}]
        prompt: list[dict[str, str]] = []
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
                return parsed
        except (ValueError, json.JSONDecodeError):
            pass
        return {
            "verified": False,
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
