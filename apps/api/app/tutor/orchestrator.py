import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator

from app.agents.harness_evaluator import PedagogyHarness
from app.agents.vision_agent import VisionParser
from app.config import Settings
from app.llm.openai_compatible import OpenAICompatibleClient
from app.knowledge.concepts import extract_explicit_concepts
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.tutor.fast_path import generate_opening, route_fast_path
from app.tutor.graph import TutorWorkflow

logger = logging.getLogger(__name__)


def sse(event: str, data: dict) -> str:
    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


class TutorOrchestrator:
    def __init__(self, settings: Settings, repository: Repository):
        self.settings = settings
        self.repository = repository
        self.llm = OpenAICompatibleClient(settings)
        self.skill_text = settings.skill_file.read_text(encoding="utf-8")
        self.vision_parser = VisionParser()
        self.harness = PedagogyHarness(settings)
        self.workflow_owner = TutorWorkflow(settings, repository)
        self.workflow = self.workflow_owner.workflow

    @staticmethod
    def _build_plan_progress(state: dict) -> str:
        learning_objective = state.get("learning_objective") or ""
        pedagogical_action = state.get("pedagogical_action") or ""
        action_descriptions = {
            "explain": "苏格拉底式引导讲解",
            "tutor": "苏格拉底式引导讲解",
            "check_step": "检查解题步骤",
            "generate_exercise": "生成练习题进行训练",
            "provide_hint": "给予提示性引导",
        }
        items = []
        if learning_objective:
            items.append(f"已识别学习目标：{learning_objective}")
        items.append(
            "采用教学策略："
            f"{action_descriptions.get(pedagogical_action, pedagogical_action or '分步引导')}"
        )
        return f"[PLAN]\n{'；'.join(items)}。"

    @staticmethod
    def _build_thinking_summary(state: dict) -> str:
        """Build a public-facing thinking summary from final state.

        Only uses deterministic fields — no LLM calls.
        Output format uses stage tags for the frontend to parse.
        """
        parts = []

        # ── PLAN ──
        pedagogical_action = state.get("pedagogical_action") or ""

        parts.append(TutorOrchestrator._build_plan_progress(state))

        # ── 隐式 RAG ──
        hits = state.get("hits", [])
        document_chunks = state.get("document_chunks", [])
        concepts = state.get("concepts", [])

        rag_items = []
        if hits:
            rag_items.append(f"已检索本地知识库（{len(hits)} 条相关知识点）")
        if concepts:
            rag_items.append(
                f"涉及概念：{'、'.join(concepts[:3])}{'等' if len(concepts) > 3 else ''}"
            )
        rag_items.append("已载入会话历史与当前掌握度评估")
        if document_chunks:
            rag_items.append(f"已参考用户绑定文档（{len(document_chunks)} 个片段）")

        parts.append(f"[隐式 RAG]\n{'；'.join(rag_items)}。")

        # ── VERIFY ──
        verify_items = []
        verifier_result = state.get("verifier_result")
        verification_result = state.get("verification_result", {})

        if isinstance(verifier_result, VerifyResult):
            if verifier_result.verified:
                if verifier_result.is_correct is True:
                    verify_items.append("SymPy 符号验证已通过")
                elif verifier_result.is_correct is False:
                    verify_items.append(
                        verifier_result.summary
                        or "SymPy 符号验证发现当前步骤与标准结果不一致"
                    )
                else:
                    verify_items.append(
                        verifier_result.summary or "SymPy 已完成符号验证"
                    )
            elif verifier_result.summary and "未触发" not in verifier_result.summary:
                if "无法判断" in verifier_result.summary:
                    verify_items.append("SymPy 无法直接判断，已升级至 Verifier LLM 验证")
                else:
                    verify_items.append(verifier_result.summary)
            else:
                verify_items.append("本轮未触发符号校验")

        if verification_result:
            if verification_result.get("verified"):
                verify_items.append("Verifier LLM 验证通过")
            else:
                verify_items.append("Verifier LLM 未能确认当前推导")

        if not verify_items:
            verify_items.append("本轮未触发符号校验")

        parts.append(f"[VERIFY]\n{'；'.join(verify_items)}。")

        # ── OUTPUT ──
        output_items = []
        route = state.get("metrics", {}).get("route", "")
        if pedagogical_action == "generate_exercise" or route == "examiner":
            output_items.append("已进入 Examiner 出题/测验阶段")
        elif route and "teacher" in str(route):
            output_items.append("已进入 Teacher 启发式讲解阶段")
        else:
            output_items.append("已开始组织回答")

        parts.append(f"[OUTPUT]\n{'；'.join(output_items)}。")

        return "\n\n".join(parts)

    @staticmethod
    def _build_learning_meta(state: dict) -> dict:
        intent_value = state.get("intent")
        intent = (
            intent_value.value
            if hasattr(intent_value, "value")
            else intent_value or "solve_step_by_step"
        )
        verifier_result = state.get("verifier_result")
        verification_result = state.get("verification_result") or {}
        verified = bool(
            verification_result.get(
                "verified",
                getattr(verifier_result, "verified", False),
            )
        )
        is_correct = verification_result.get(
            "is_correct",
            getattr(verifier_result, "is_correct", None),
        )
        verifier_summary = verification_result.get(
            "summary",
            getattr(verifier_result, "summary", ""),
        )
        mistake = state.get("mistake")
        return {
            "intent": intent,
            "subject": state.get("detected_subject")
            or state.get("subject")
            or "auto",
            "concepts": state.get("concepts", []),
            "verified": verified,
            "is_correct": is_correct,
            "mistake": getattr(mistake, "label", mistake),
            "verifier_summary": verifier_summary or "",
            "hint_level": state.get("hint_level", 0),
            "mastery_score": state.get("mastery_score", 0.5),
            "mastery_label": state.get("mastery_label_str", "一般"),
            "mastery_delta": state.get("mastery_delta", 0.0),
            "pedagogical_action": state.get("pedagogical_action", ""),
            "learning_objective": state.get("learning_objective", ""),
            "route": state.get("metrics", {}).get("route", ""),
        }

    async def stream_reply(
        self,
        session_id: str,
        user_id: str,
        message: str,
        subject: str = "auto",
        mode: str = "socratic",
        user_api_key: str | None = None,
        model: str | None = None,
        requested_hint: bool = False,
        image_urls: list[str] | None = None,
    ) -> AsyncIterator[str]:
        request_started = time.perf_counter()
        route = route_fast_path(message, mode, subject)
        opening = generate_opening(route)
        opening_ms = round(
            (time.perf_counter() - request_started) * 1000,
            2,
        )

        yield sse(
            "opening",
            {
                "content": f"{opening}\n\n",
                "opening_ms": opening_ms,
            },
        )

        initial_state = {
            "message": message,
            "session_id": session_id,
            "user_id": user_id,
            "subject": subject,
            "mode": mode,
            "user_api_key": user_api_key,
            "model": model,
            "requested_hint": requested_hint,
            "image_urls": image_urls,
            "intent": route.intent,
            "detected_subject": route.subject,
            "pedagogical_action": route.pedagogical_action,
            "learning_objective": route.learning_objective,
            "verification_mode": route.verification_mode.value,
            "confidence": route.confidence,
            "requires_policy_fallback": route.requires_policy_fallback,
            "hits": [],
            "document_chunks": [],
            "verifier_result": VerifyResult(
                False,
                None,
                "本轮未触发自动验证。",
            ),
            "verification_result": {},
            "mistake": None,
            "concepts": [],
            "mastery_score": 0.5,
            "mastery_delta": 0.0,
            "mastery_label_str": "一般",
            "hint_level": 0,
            "messages": [],
            "thinking_steps": [],
            "final_output": "",
            "thinking_chain": "",
            "metrics": {
                "opening_ms": opening_ms,
                "fast_context_ms": 0.0,
                "local_rag_ms": 0.0,
                "symbolic_verify_ms": 0.0,
                "policy_fallback_ms": 0.0,
                "verifier_ms": 0.0,
                "teacher_first_token_ms": 0.0,
                "total_ms": 0.0,
                "llm_call_count": 0,
                "route": "",
            },
        }

        queue: asyncio.Queue[str] = asyncio.Queue()
        first_token_time: float | None = None
        plan_progress = self._build_plan_progress(initial_state)

        async def on_token(event_str: str) -> None:
            nonlocal first_token_time
            if first_token_time is None:
                first_token_time = time.perf_counter()
            await queue.put(event_str)

        async def on_thinking(event_str: str) -> None:
            await queue.put(event_str)

        async def on_progress(content: str) -> None:
            normalized = content.strip()
            if normalized:
                await queue.put(
                    sse("thinking", {"content": f"{normalized}\n\n"})
                )

        config = {
            "configurable": {
                "thread_id": session_id,
                "on_token": on_token,
                "on_thinking": on_thinking,
                "on_progress": on_progress,
            }
        }
        task = asyncio.create_task(
            self.workflow.ainvoke(initial_state, config=config)
        )
        queue_get: asyncio.Task[str] | None = None

        yield sse("thinking", {"content": f"{plan_progress}\n\n"})

        try:
            while True:
                if not queue.empty():
                    yield queue.get_nowait()
                    continue
                if task.done():
                    break

                queue_get = asyncio.create_task(queue.get())
                done, _ = await asyncio.wait(
                    {task, queue_get},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if queue_get in done:
                    yield queue_get.result()
                    queue_get = None
                elif task in done:
                    queue_get.cancel()
                    await asyncio.gather(
                        queue_get,
                        return_exceptions=True,
                    )
                    queue_get = None

            final_state = await task
            while not queue.empty():
                yield queue.get_nowait()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                "Tutor workflow failed: %s",
                exc,
                exc_info=True,
            )
            yield sse(
                "error",
                {
                    "message": "本轮生成暂时失败，请稍后重试。",
                    "recoverable": True,
                },
            )
            return
        finally:
            if queue_get and not queue_get.done():
                queue_get.cancel()
                await asyncio.gather(queue_get, return_exceptions=True)
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

        # Build thinking summary and calculate elapsed_ms
        thinking_summary = self._build_thinking_summary(final_state)
        if first_token_time is not None:
            thinking_elapsed_ms = round((first_token_time - request_started) * 1000)
        else:
            thinking_elapsed_ms = round((time.perf_counter() - request_started) * 1000)

        yield sse(
            "thinking_end",
            {
                "chain": final_state.get("thinking_chain", ""),
                "summary": thinking_summary,
                "elapsed_ms": thinking_elapsed_ms,
            },
        )

        visible_output = (
            f"{opening}\n\n{final_state.get('final_output', '')}"
        ).strip()
        explicit_concepts = extract_explicit_concepts(
            f"{message}\n{visible_output}"
        )
        if explicit_concepts:
            final_state = {
                **final_state,
                "concepts": explicit_concepts,
            }
        learning_meta = self._build_learning_meta(final_state)
        intent = learning_meta["intent"]
        message_id = await asyncio.to_thread(
            self.repository.add_message,
            session_id,
            "assistant",
            visible_output,
            intent,
            thinking_summary,
            thinking_elapsed_ms,
            learning_meta,
        )
        metrics = dict(final_state.get("metrics", {}))
        metrics["total_ms"] = round(
            (time.perf_counter() - request_started) * 1000,
            2,
        )
        workflow_owner = getattr(self, "workflow_owner", None)
        if workflow_owner is not None:
            workflow_owner.schedule_semantic_enrichment(
                message,
                route.subject,
                user_api_key,
            )
        yield sse(
            "done",
            {
                "message_id": message_id,
                "metrics": metrics,
            },
        )
