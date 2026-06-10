import json
import asyncio
from typing import AsyncIterator

from app.config import Settings
from app.llm.openai_compatible import OpenAICompatibleClient
from app.memory.repository import Repository
from app.agents.vision_agent import VisionParser
from app.agents.harness_evaluator import PedagogyHarness
from app.tutor.graph import TutorWorkflow


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class TutorOrchestrator:
    def __init__(self, settings: Settings, repository: Repository):
        self.settings = settings
        self.repository = repository
        self.llm = OpenAICompatibleClient(settings)
        self.skill_text = settings.skill_file.read_text(encoding="utf-8")
        self.vision_parser = VisionParser()
        self.harness = PedagogyHarness(settings)
        self.workflow = TutorWorkflow(settings, repository).workflow

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
        # Initialize LangGraph AgentState
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
            "intent": None,
            "detected_subject": None,
            "hits": [],
            "document_chunks": [],
            "verifier_result": None,
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
            "loop_count": 0,
            "next_action": "",
        }

        queue = asyncio.Queue()

        async def on_token(event_str: str):
            await queue.put(event_str)

        async def on_thinking(event_str: str):
            await queue.put(event_str)

        config = {
            "configurable": {
                "thread_id": session_id,
                "on_token": on_token,
                "on_thinking": on_thinking
            }
        }

        # Run the workflow in a background task to stream events as they happen
        task = asyncio.create_task(
            self.workflow.ainvoke(initial_state, config=config)
        )

        while not task.done() or not queue.empty():
            while not queue.empty():
                yield queue.get_nowait()
            if task.done():
                break
            await asyncio.sleep(0.01)

        # Retrieve final state and raise any graph exceptions
        final_state = await task

        # Stream leftover events
        while not queue.empty():
            yield queue.get_nowait()

        # Emit thinking_end event
        yield sse("thinking_end", {"chain": final_state.get("thinking_chain", "")})

        # Save assistant's final response to DB
        intent_val = final_state.get("intent")
        intent_str = intent_val.value if intent_val else "solve_step_by_step"
        message_id = self.repository.add_message(
            session_id,
            "assistant",
            final_state.get("final_output", ""),
            intent_str
        )

        # Emit done event
        yield sse("done", {"message_id": message_id})
