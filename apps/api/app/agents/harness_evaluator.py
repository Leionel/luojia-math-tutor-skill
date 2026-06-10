import json
from app.config import Settings
from app.llm.openai_compatible import OpenAICompatibleClient

class PedagogyHarness:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = OpenAICompatibleClient(settings)

    async def evaluate_response(self, sample: dict, ai_response: str, user_api_key: str | None = None, model: str | None = None) -> dict:
        prompt = f"""
You are a pedagogical evaluation harness.
Your task is to evaluate the AI tutor's response to the student's solution.
You need to evaluate the AI response against specific rubrics:
1. `direct_answer_leak`: True if the AI directly gave the correct answer ('{sample.get("ground_truth", {}).get("correct_answer")}') instead of guiding the student.
2. `sympy_verifiable`: True if the math formulas in the AI's response are well-formed and could potentially be verified by a CAS like SymPy (e.g. standard LaTeX).
3. `action_aligned`: True if the AI's response aligns with the expected pedagogical action ('{sample.get("pedagogical_action")}').

Benchmark Sample Context:
- Question: {sample.get("question")}
- Student Solution: {sample.get("student_solution")}
- Conversation History: {sample.get("conversation_history")}
- Pedagogical Action Expected: {sample.get("pedagogical_action")}
- Ideal Response: {sample.get("ground_truth", {}).get("ideal_response")}

AI's response:
{ai_response}

You must output your evaluation strictly as a JSON object with the following schema:
{{
    "passed": <boolean, true if the AI response is pedagogically sound (no leak and action aligned), false otherwise>,
    "reason": "<string, explanation of the evaluation>",
    "suggested_fix": "<string, how to fix the AI response if it failed, else empty string>",
    "direct_answer_leak": <boolean>,
    "sympy_verifiable": <boolean>,
    "action_aligned": <boolean>
}}

Return ONLY the JSON object. Do not wrap it in markdown code blocks.
"""
        messages = [
            {"role": "system", "content": "You are a pedagogical evaluator. Output only valid JSON."},
            {"role": "user", "content": prompt}
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
                
            return json.loads(result.strip())
        except Exception as e:
            return {
                "passed": False,
                "reason": f"Evaluation failed due to exception: {str(e)}",
                "suggested_fix": "",
                "direct_answer_leak": False,
                "sympy_verifiable": False,
                "action_aligned": False
            }
