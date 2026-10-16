import asyncio
import json
import os
import shutil
import sys
from datetime import datetime, timezone

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
    session_id = sample["id"]
    user_id = "benchmark_user"
    prompt = f"Question: {sample['question']}\nMy solution: {sample['student_solution']}"
    result = {"id": session_id, "sample": sample, "ai_response": "", "error": None, "evaluation": None}

    try:
        ai_response_chunks = []
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
        result["ai_response"] = "".join(ai_response_chunks)
    except Exception as e:
        # A failed generation is recorded and left unscored, never scored as a
        # silent failure that would distort the pass rate.
        result["error"] = f"stream_reply failed: {e}"
        return result

    if not result["ai_response"].strip():
        result["error"] = "stream_reply produced an empty ai_response"
        return result

    try:
        result["evaluation"] = await harness.evaluate_response(sample, result["ai_response"])
    except Exception as e:
        result["error"] = f"harness evaluation failed: {e}"

    return result

def archive_previous_run(output_file: str, history_dir: str) -> None:
    if os.path.exists(output_file):
        os.makedirs(history_dir, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        target = os.path.join(history_dir, stamp, os.path.basename(output_file))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.move(output_file, target)
        print(f"Archived previous results to {target}")

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
    history_dir = os.path.join(project_root, "results", "history")

    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return

    # One run = one file: the previous run is archived, never appended to, so
    # line count always equals the number of benchmark samples.
    archive_previous_run(output_file, history_dir)

    samples = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))

    out_f = open(output_file, "w", encoding="utf-8")

    sem = asyncio.Semaphore(5)

    async def process_with_sem(i, sample):
        async with sem:
            print(f"Evaluating [{i+1}/{len(samples)}] {sample['id']}...")
            result = await evaluate_sample(orchestrator, harness, sample)
            out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
            out_f.flush()
            return result

    try:
        tasks = [process_with_sem(i, sample) for i, sample in enumerate(samples)]
        results = await asyncio.gather(*tasks)
    finally:
        out_f.close()

    # Summary: error rows are excluded from the scored denominator.
    errors = [r for r in results if r.get("error")]
    scored = [r for r in results if not r.get("error")]
    passed_count = sum(1 for r in scored if (r.get("evaluation") or {}).get("passed", False))
    print(f"\nEvaluation Complete! Passed: {passed_count}/{len(scored)} scored, {len(errors)} unscored (errors)")
    for r in errors:
        print(f"  [unscored] {r['id']}: {r['error']}")

if __name__ == "__main__":
    asyncio.run(main())
