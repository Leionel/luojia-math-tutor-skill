import json
import logging
from dataclasses import dataclass

from app.llm.openai_compatible import OpenAICompatibleClient
from app.tutor.intent_router import ACTION_BY_INTENT, Intent, PedagogicalAction


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PolicyDecision:
    intent: Intent
    action: PedagogicalAction
    confidence: float
    uncertain: bool

class PolicyRouter:
    def __init__(self, llm: OpenAICompatibleClient):
        self.llm = llm

    async def decide_route(
        self,
        message: str,
        fallback_intent: Intent,
        user_api_key: str | None = None,
        model: str | None = None,
    ) -> PolicyDecision:
        schema = {
            "intent": [item.value for item in Intent],
            "action": [item.value for item in PedagogicalAction],
            "confidence": "number 0..1",
            "uncertain": "boolean",
        }
        messages = [
            {
                "role": "user",
                "content": (
                    "你是数学辅导请求的结构化路由器，不要解题。"
                    "分析否定、多意图和口语表达，只输出 JSON。\n"
                    f"schema={json.dumps(schema, ensure_ascii=False)}\n"
                    f"student_message={json.dumps(message, ensure_ascii=False)}"
                ),
            }
        ]
        try:
            result = await self.llm.chat_completion(
                messages,
                api_key=user_api_key,
                model=model,
            )
            start = result.index("{")
            end = result.rindex("}") + 1
            data = json.loads(result[start:end])
            intent = Intent(str(data["intent"]))
            action = PedagogicalAction(str(data["action"]))
            confidence = max(0.0, min(1.0, float(data.get("confidence", 0.0))))
            uncertain = bool(data.get("uncertain", confidence < 0.7))
            return PolicyDecision(intent, action, confidence, uncertain)
        except Exception as exc:
            logger.warning("PolicyRouter fell back to deterministic route: %s", exc)
            return PolicyDecision(
                fallback_intent,
                ACTION_BY_INTENT[fallback_intent],
                0.0,
                True,
            )

    async def decide_action(
        self,
        message: str,
        user_api_key: str | None = None,
        model: str | None = None,
    ) -> PedagogicalAction:
        decision = await self.decide_route(
            message,
            Intent.SOLVE_STEP_BY_STEP,
            user_api_key,
            model,
        )
        return decision.action
