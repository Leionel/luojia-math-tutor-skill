import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator

from app.agents.harness_evaluator import PedagogyHarness
from app.agents.vision_agent import VisionParser
from app.config import Settings
from app.llm.openai_compatible import OpenAICompatibleClient
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
                "content": opening,
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

        async def on_token(event_str: str) -> None:
            await queue.put(event_str)

        async def on_thinking(event_str: str) -> None:
            await queue.put(event_str)

        config = {
            "configurable": {
                "thread_id": session_id,
                "on_token": on_token,
                "on_thinking": on_thinking,
            }
        }
        task = asyncio.create_task(
            self.workflow.ainvoke(initial_state, config=config)
        )
        queue_get: asyncio.Task[str] | None = None

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

        yield sse(
            "thinking_end",
            {"chain": final_state.get("thinking_chain", "")},
        )

        intent_value = final_state.get("intent")
        intent = (
            intent_value.value
            if intent_value
            else "solve_step_by_step"
        )
        message_id = await asyncio.to_thread(
            self.repository.add_message,
            session_id,
            "assistant",
            final_state.get("final_output", ""),
            intent,
        )
        metrics = dict(final_state.get("metrics", {}))
        metrics["total_ms"] = round(
            (time.perf_counter() - request_started) * 1000,
            2,
        )
        yield sse(
            "done",
            {
                "message_id": message_id,
                "metrics": metrics,
            },
        )
