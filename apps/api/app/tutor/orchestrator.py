import asyncio
import json
import logging
import time
import httpx
from collections.abc import AsyncIterator

from app.config import Settings
from app.search.policy import decide_search
from app.search.web_search import search_status_text
from app.llm.openai_compatible import OpenAICompatibleClient
from app.knowledge.concepts import extract_explicit_concepts
from app.math_tools.verifier import VerifyResult
from app.memory.repository import Repository
from app.observability import current_request_id
from app.tutor.fast_path import generate_opening, route_fast_path
from app.tutor.graph import TutorWorkflow
from app.tutor.prompt_policy import load_teaching_prompt

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
        self.skill_text = load_teaching_prompt(settings.skill_file)
        self.workflow_owner = TutorWorkflow(settings, repository)
        self.workflow = self.workflow_owner.workflow

    @staticmethod
    def _build_plan_progress(state: dict) -> str:
        learning_objective = state.get("learning_objective") or ""
        pedagogical_action = state.get("pedagogical_action") or ""
        action_descriptions = {
            "explain": "讲解概念或解题过程",
            "hint": "提供当前步骤的提示",
            "ask_question": "核对步骤并提出针对性问题",
            "review_concept": "复习相关概念",
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
        if state.get("root_diagnosis"):
            report = state["root_diagnosis"]
            return f"[PLAN]\n核对所提交的求根轨迹与目标。\n\n[VERIFY]\n{report['summary']}\n\n[OUTPUT]\n已输出受控数值反馈；显示回执后记录过程证据。"
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
        rag_items.append("已参考会话历史；掌握度估计可能包含初始默认值")
        if document_chunks:
            rag_items.append(f"已参考文档与外部资料（{len(document_chunks)} 个片段）")

        if state.get("web_search_report"):
            rag_items.append(search_status_text(state["web_search_report"]))
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
                verdict = verification_result.get("is_correct")
                verify_items.append(
                    "推理审查认为本步正确（非确定性证明）" if verdict is True else
                    "推理审查发现需要修正之处" if verdict is False else
                    "推理审查完成，正误尚不能确定"
                )
            else:
                verify_items.append("推理审查未能确认当前推导")

        if not verify_items:
            verify_items.append("本轮未触发符号校验")

        parts.append(f"[VERIFY]\n{'；'.join(verify_items)}。")

        # ── OUTPUT ──
        output_items = []
        route = state.get("metrics", {}).get("route", "")
        if pedagogical_action == "generate_exercise" or route == "examiner":
            output_items.append("正在生成练习题")
        elif route and "teacher" in str(route):
            output_items.append("正在组织讲解")
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
        concepts = state.get("concepts", [])
        concept_items_by_label = {
            str(item.get("label")): item
            for item in state.get("concept_items", [])
            if isinstance(item, dict) and item.get("label")
        }
        concept_items = []
        for index, concept in enumerate(concepts):
            item = dict(concept_items_by_label.get(concept, {}))
            item.setdefault("id", f"concept:{concept}")
            item["label"] = concept
            item["role"] = "primary" if index == 0 else "related"
            item["assessed"] = bool(
                index == 0
                and verified
                and is_correct is not None
                and intent == "check_student_step"
            )
            item.setdefault("path", [])
            item.setdefault("description", "")
            item.setdefault("source", "rule")
            item.setdefault("evidence", "根据本轮题意识别")
            item.setdefault("prerequisites", [])
            concept_items.append(item)
        return {
            "intent": intent,
            "teaching_mode": state.get("mode", "socratic"),
            "web_search": state.get("web_search_report"),
            "subject": state.get("detected_subject")
            or state.get("subject")
            or "auto",
            "concepts": concepts,
            "concept_items": concept_items,
            "verified": verified,
            "verification_kind": "llm_review" if verification_result else "symbolic" if getattr(verifier_result, "verified", False) else "none",
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
        web_search: bool = False,
        web_search_mode: str = "auto",
        reasoning_effort: str = "medium",
        root_submission: dict | None = None,
    ) -> AsyncIterator[str]:
        request_started = time.perf_counter()
        request_id = current_request_id()
        initial_mastery = getattr(
            getattr(self, "settings", None),
            "initial_mastery",
            0.5,
        )
        route = route_fast_path(message, mode, subject)
        search = decide_search(message, web_search_mode, web_search)
        opening = "我先用受控数值规则核对你提交的求根过程。" if root_submission else "我先识别图片中的题目，核对后再继续。" if image_urls else generate_opening(route)
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
            "root_submission": root_submission,
            "message": message,
            "original_message": message,
            "session_id": session_id,
            "user_id": user_id,
            "subject": subject,
            "mode": mode,
            "user_api_key": user_api_key,
            "model": model,
            "requested_hint": requested_hint,
            "image_urls": image_urls,
            "web_search": search.enabled,
            "web_search_reason": search.reason,
            "external_fact_question": search.factual,
            "reasoning_effort": reasoning_effort,
            "vision_result": {},
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
            "concept_items": [],
            "mastery_score": initial_mastery,
            "mastery_delta": 0.0,
            "mastery_label_str": "一般",
            "hint_level": 0,
            "messages": [],
            "thinking_steps": [],
            "final_output": "",
            "thinking_chain": "",
            "metrics": {
                "request_id": request_id,
                "opening_ms": opening_ms,
                "fast_context_ms": 0.0,
                "local_rag_ms": 0.0,
                "symbolic_verify_ms": 0.0,
                "policy_fallback_ms": 0.0,
                "verifier_ms": 0.0,
                "teacher_first_token_ms": 0.0,
                "vision_parse_ms": 0.0,
                "sandbox_tool_calls": 0,
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
            code, message, recoverable = "generation_failed", "本轮生成暂时失败，请稍后重试。", True
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code in (401, 403):
                code, message, recoverable = "model_auth_failed", "模型服务鉴权失败，请核对所选模型、接口地址与 API Key。", False
            elif isinstance(exc, (httpx.TimeoutException, asyncio.TimeoutError)):
                code, message = "model_timeout", "模型响应超时，本轮未生成完整回答；可降低运思强度后重试。"
            elif isinstance(exc, httpx.ConnectError):
                code, message = "model_unreachable", "无法连接模型服务，请检查网络与接口地址。"
            elif isinstance(exc, (ValueError, KeyError)) and root_submission:
                code, message = "root_attempt_invalid", "求根 episode 或修订输入无效；请核对任务条件，或开始新的练习。"
            # Safe error metadata survives refresh; it never asserts a completed answer.
            failure_meta = {"error": {"code": code, "message": message}, "verified": False, "is_correct": None, "intent": "generation_failed", "verification_kind": "none", "subject": subject, "concepts": [], "mistake": None, "verifier_summary": "本轮未完成"}
            failure_id = None
            try:
                failure_id = await asyncio.to_thread(self.repository.add_message, session_id, "assistant", f"{opening}\n\n本轮未完成：{message}", "generation_failed", "本轮生成失败，尚未完成验证。", None, failure_meta)
            except Exception:
                logger.exception("Could not persist failed response metadata")
            yield sse("error", {"message": message, "code": code, "recoverable": recoverable, "message_id": failure_id})
            return
        finally:
            if queue_get and not queue_get.done():
                queue_get.cancel()
                await asyncio.gather(queue_get, return_exceptions=True)
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

        # Build thinking summary and calculate elapsed_ms
        awaiting_vision = final_state.get("awaiting_vision_confirmation", False)
        thinking_summary = "图片核对阶段，本轮未开始解题或评估掌握度。" if awaiting_vision else self._build_thinking_summary(final_state)
        if awaiting_vision:
            await asyncio.to_thread(self.repository.ensure_user, user_id)
            await asyncio.to_thread(self.repository.add_message, session_id, "user", message)
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
        if explicit_concepts and not awaiting_vision:
            final_state = {
                **final_state,
                "concepts": explicit_concepts,
            }
        learning_meta = self._build_learning_meta(final_state)
        if final_state.get("root_diagnosis"):
            report = final_state["root_diagnosis"]
            learning_meta.update(root_diagnosis=report, verification_kind="root_oracle",
                                 verified=report["status"] in ("supported", "contradicted"),
                                 is_correct=True if report["complete"] else False if report["status"] == "contradicted" else None,
                                 verifier_summary=report["summary"], mastery_delta=0, hint_level=report["help_level"])
        if awaiting_vision:
            parsed = final_state.get("vision_result", {})
            draft = "\n\n".join(part for part in (
                str(parsed.get("problem_text") or ""),
                "\n".join(f"$${item}$$" for item in parsed.get("latex", [])),
            ) if part)
            learning_meta = {"intent": "vision_confirmation", "subject": subject,
                             "verified": False, "is_correct": None, "concepts": [],
                             "concept_items": [], "awaiting_confirmation": True,
                             "vision_draft": draft, "verification_kind": "none",
                             "mistake": None, "verifier_summary": "图片核对阶段，尚未开始解题"}
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
        yield sse("meta_update", learning_meta)
        metrics = dict(final_state.get("metrics", {}))
        metrics["total_ms"] = round(
            (time.perf_counter() - request_started) * 1000,
            2,
        )
        workflow_owner = getattr(self, "workflow_owner", None)
        if workflow_owner is not None and not awaiting_vision and not search.factual and not root_submission:
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
