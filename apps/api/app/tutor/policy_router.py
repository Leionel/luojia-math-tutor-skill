import json
from enum import Enum
from app.llm.openai_compatible import OpenAICompatibleClient

class PedagogicalAction(str, Enum):
    HINT = "hint"
    ASK_QUESTION = "ask_question"
    EXPLAIN = "explain"
    REVIEW_CONCEPT = "review_concept"
    GENERATE_EXERCISE = "generate_exercise"

class PolicyRouter:
    def __init__(self, llm: OpenAICompatibleClient):
        self.llm = llm

    async def decide_action(
        self,
        message: str,
        user_api_key: str | None = None,
        model: str | None = None
    ) -> PedagogicalAction:
        prompt = f"""
You are the Pedagogical Policy Router for an AI Math Tutor.
Your job is to strictly analyze the student's input and select the BEST single pedagogical action.
Do NOT attempt to solve the math problem. Just decide the action.

The valid actions are:
- hint: Provide a subtle clue to unblock the student, without giving away the direct next step. Best when the student is stuck but on the right track.
- ask_question: Ask a guiding or probing question to make the student reflect on their logic. Best when the student made a mistake or skipped a step.
- explain: Directly explain a concept or walk through a calculation. Use only when the student explicitly asks for an explanation or is completely lost.
- review_concept: Review a previously learned fundamental concept that the student seems to have forgotten or misunderstood.
- generate_exercise: Create a new practice problem for the student to try.

Student's current input:
{message}

You must output ONLY a valid JSON object with the following schema:
{{
    "reasoning": "<string, briefly explain why this action is best>",
    "action": "<string, exactly one of: hint, ask_question, explain, review_concept, generate_exercise>"
}}
"""
        messages = [
            {"role": "system", "content": "You are a pedagogical policy router. Output only valid JSON."},
            {"role": "user", "content": prompt.strip()}
        ]
        
        try:
            result = await self.llm.chat_completion(messages, api_key=user_api_key, model=model)
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            elif result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
                
            data = json.loads(result.strip())
            action_str = data.get("action", "hint").lower()
            try:
                return PedagogicalAction(action_str)
            except ValueError:
                return PedagogicalAction.HINT
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"PolicyRouter failed: {e}")
            return PedagogicalAction.HINT
