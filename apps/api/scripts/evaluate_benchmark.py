import asyncio
import json
import os
import sys

# Ensure root path is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "apps", "api"))

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, "apps", "api", ".env"))

from app.config import Settings
from app.memory.repository import Repository
from app.tutor.orchestrator import TutorOrchestrator
from app.agents.harness_evaluator import PedagogyHarness

async def mock_create_embedding(self, text: str, api_key: str | None = None, model: str | None = None) -> list[float]:
    return [0.0] * 1536

async def evaluate_sample(orchestrator: TutorOrchestrator, harness: PedagogyHarness, sample: dict) -> dict:
    # 1. Setup session in DB
    session_id = sample["id"]
    user_id = "benchmark_user"
    
    # Pre-populate conversation history if any
    # Note: Depending on orchestrator logic, we might just inject history directly or rely on the agent seeing the previous messages.
    # We will simulate the interaction by sending the student_solution + question as the prompt.
    prompt = f"Question: {sample['question']}\nMy solution: {sample['student_solution']}"
    
    # 2. Get Tutor AI Response
    ai_response_chunks = []
    try:
        async for chunk in orchestrator.stream_reply(
            session_id=session_id,
            user_id=user_id,
            message=prompt,
            subject=sample.get("subject", "auto")
        ):
            if chunk.startswith("event: message"):
                data_str = chunk.split("data: ", 1)[1].strip()
                data = json.loads(data_str)
                if data.get("type") == "message":
                    ai_response_chunks.append(data.get("content", ""))
    except Exception as e:
        print(f"Error during stream_reply for {session_id}: {e}")

    ai_response = "".join(ai_response_chunks)
    
    # 3. Evaluate with PedagogyHarness
    evaluation = await harness.evaluate_response(sample, ai_response)
    
    return {
        "id": session_id,
        "sample": sample,
        "ai_response": ai_response,
        "evaluation": evaluation
    }

async def main():
    settings = Settings(llm_api_key=os.environ.get("LLM_API_KEY"))
    # Use an in-memory DB or a specific test DB so we don't pollute prod
    settings.database_url = "sqlite:///./benchmark_eval.db"
    
    # Global mock to prevent any instance from trying to hit network for embeddings
    from app.llm.openai_compatible import OpenAICompatibleClient
    OpenAICompatibleClient.create_embedding = mock_create_embedding
    
    repository = Repository(settings)
    orchestrator = TutorOrchestrator(settings, repository)
    harness = PedagogyHarness(settings)
    
    input_file = os.path.join(project_root, "data", "LuojiaMathBench_v8.jsonl")
    output_file = os.path.join(project_root, "results", "v8_eval_results.jsonl")
    
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return

    # Collect all samples first
    samples = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
                
    # Run with concurrency
    sem = asyncio.Semaphore(5)
    
    async def process_with_sem(i, sample):
        async with sem:
            print(f"Evaluating [{i+1}/{len(samples)}] {sample['id']}...")
            result = await evaluate_sample(orchestrator, harness, sample)
            # Save incrementally
            with open(output_file, "a", encoding="utf-8") as out_f:
                out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
            return result
            
    tasks = [process_with_sem(i, sample) for i, sample in enumerate(samples)]
    results = await asyncio.gather(*tasks)
                
    # Print summary
    passed_count = sum(1 for r in results if r["evaluation"].get("passed", False))
    print(f"\nEvaluation Complete! Passed: {passed_count}/{len(results)}")

if __name__ == "__main__":
    asyncio.run(main())
