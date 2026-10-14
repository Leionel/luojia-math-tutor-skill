"""Offline R2 Newton D0/D1 application-path pairs. No live option or quality scores."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from s5_quality import digest, load_json

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evaluation/r1/a0-development-cases.json"
RUBRIC = ROOT / "evaluation/r2/newton-pair-rubric-v1.json"
MESSAGE = "请检查我选中的原话，区分能确认的步骤、错误推广和未知条件。"
FIXED_REPLY = "[OUTPUT] 离线固定回复：本轮用于检查保存原话、来源与交付链；数学意见尚未评分。请说明你的结论适用什么范围。"


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def runtime(messages):
    developer = next(row["content"] for row in messages if row["role"] == "developer" and "[RUNTIME_CONTEXT]\n" in row["content"])
    return json.loads(developer.split("[RUNTIME_CONTEXT]\n", 1)[1].split("\n[/RUNTIME_CONTEXT]", 1)[0])


def pair_matches(d0, d1):
    """Fail closed if anything beyond the declared exact-check intervention differs."""
    left, right = runtime(d0), runtime(d1)
    evidence = right.get("learning_task", {}).pop("exact_check", None)
    if evidence is None or "exact_check" in left.get("learning_task", {}) or left != right:
        return False
    # Compare the surrounding instructions and messages as well as the runtime.
    def without_runtime(messages):
        result = deepcopy(messages)
        for row in result:
            if row["role"] == "developer" and "[RUNTIME_CONTEXT]\n" in row["content"]:
                before, remainder = row["content"].split("[RUNTIME_CONTEXT]\n", 1)
                after = remainder.split("\n[/RUNTIME_CONTEXT]", 1)[1]
                row["content"] = before + "[RUNTIME_CONTEXT]" + after
        return result
    return without_runtime(d0) == without_runtime(d1)


def worker(output):
    for key in list(os.environ):
        if "KEY" in key or "TOKEN" in key or key.startswith(("LLM_", "MINERU_", "DATABASE_", "COURSE_")):
            os.environ.pop(key, None)
    os.environ["LUOJIA_NO_DOTENV"] = "1"
    sys.path.insert(0, str(ROOT / "apps/api"))
    from unittest.mock import patch
    import socket
    import httpx
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from starlette.testclient import _TestClientTransport
    from app.auth import Principal, get_principal
    from app.config import Settings
    from app.memory.repository import Repository
    from app.knowledge.course_store import CourseStore
    from app.knowledge.course_service import CourseService
    from app.tutor.learning_workspace import LearningWorkspace
    from app.tutor.learning_context import LearningContextRef, NewtonActivityClaimRef, resolve_learning_context
    from app.tutor.newton_activity import NewtonActivity, ACTIVITY_ID, ACTIVITY_VERSION
    from app.tutor.orchestrator import TutorOrchestrator
    from app.api import routes_tutor
    from app.main_deps import get_learning_workspace, get_orchestrator, get_app_settings

    original_send = httpx.Client.send
    def local_send(client, request, *args, **kwargs):
        if isinstance(client._transport, _TestClientTransport) and request.url.host == "testserver":
            return original_send(client, request, *args, **kwargs)
        raise RuntimeError("R2 offline capture denies outbound HTTP")
    async def deny_async(*args, **kwargs):
        raise RuntimeError("R2 offline capture denies outbound HTTP")
    def deny_socket(*args, **kwargs):
        raise RuntimeError("R2 offline capture denies outbound sockets")

    material = load_json(CASES)
    if material.get("status") != "agent_prepared_only":
        raise ValueError("public development status changed")
    cases = [row for row in material["cases"] if row["id"] in {"N01", "N02"}]
    if len(cases) != 2:
        raise ValueError("expected N01/N02 public cases")
    rubric = load_json(RUBRIC)
    if (rubric.get("version") != "r2-newton-pair-rubric-v1" or rubric.get("status") != "agent_prepared_only"
            or rubric.get("human_author_review") != "pending" or rubric.get("independent_human_review") != "pending"
            or {row["id"] for row in rubric.get("cases", [])} != {"N01", "N02"}
            or len(rubric["cases"]) != 2 or any(row.get("ratings") is not None for row in rubric["cases"])):
        raise ValueError("offline capture cannot promote or score a review rubric")
    records = []
    with patch.object(httpx.Client, "send", local_send), patch.object(httpx.AsyncClient, "send", deny_async):
        for case in cases:
            for arm in ("D0", "D1"):
                with tempfile.TemporaryDirectory(prefix="r2-pair-") as temporary:
                    folder = Path(temporary)
                    settings = Settings(database_url=f"sqlite:///{folder / 'student.db'}", llm_api_key="", typed_math_tools_enabled=False)
                    repository = Repository(settings)
                    course = CourseService(store=CourseStore(str(folder / "course.db")))
                    try:
                        workspace = LearningWorkspace(course, repository)
                        owner = "r2-synthetic-student"
                        clean = repository.list_mastery(owner) == [] and repository.list_user_mistakes(owner) == []
                        activity = NewtonActivity(workspace)
                        activity.predict(owner, "pair-predict", "我猜会逐渐收敛", "合成开发输入")
                        state = activity.reveal(owner, "pair-reveal", "observe")
                        for index in range(8):
                            if state["observation_complete"]:
                                break
                            state = activity.step(owner, f"pair-step-{index}", index)
                        if not state["observation_complete"]:
                            raise ValueError("activity was not fully revealed")
                        run = state["run"]
                        activity.explain(owner, "pair-explain", run["id"], run["input_hash"], case["student_claim"])
                        ref = LearningContextRef(kind="root_lab", record_id=run["id"],
                            **{key: run[key] for key in ("input_hash", "runner_version", "graph_revision")},
                            activity_claim=NewtonActivityClaimRef(activity_id=ACTIVITY_ID, activity_version=ACTIVITY_VERSION,
                                claim_kind="explanation", request_id="pair-explain", revision_count=0))
                        def resolve(work, actor, reference):
                            snapshot = resolve_learning_context(work, actor, reference)
                            if arm == "D0":
                                snapshot.pop("exact_check", None)
                            return snapshot
                        session = repository.create_session(owner, "数值分析")["session_id"]
                        tutor = TutorOrchestrator(settings, repository)
                        async def no_hits(*args, **kwargs):
                            return None, 0.0
                        tutor.workflow_owner.context_collector._collect_local_hits = no_hits
                        tutor.workflow_owner.schedule_semantic_enrichment = lambda *args, **kwargs: None
                        inputs, calls = [], []
                        async def fixed_stream(messages, **kwargs):
                            inputs.append(deepcopy(messages))
                            calls.append("fixed_teacher_stream")
                            yield {"type": "content", "content": FIXED_REPLY}
                        async def fixed_review(*args, **kwargs):
                            calls.append("fixed_auxiliary_completion")
                            return '{"verified":false,"is_correct":null,"reason":"offline fixture","summary":"pending"}'
                        tutor.workflow_owner.llm.stream = fixed_stream
                        tutor.workflow_owner.llm.chat_completion = fixed_review
                        app = FastAPI()
                        app.include_router(routes_tutor.router)
                        app.dependency_overrides[get_principal] = lambda: Principal(owner, True)
                        app.dependency_overrides[get_learning_workspace] = lambda: workspace
                        app.dependency_overrides[get_orchestrator] = lambda: tutor
                        app.dependency_overrides[get_app_settings] = lambda: settings
                        started = time.monotonic()
                        with patch("app.knowledge.course_service.get_course_service", return_value=course), \
                             patch("app.tutor.orchestrator.resolve_learning_context", resolve), TestClient(app) as client:
                            with patch.object(socket.socket, "connect", deny_socket), patch.object(socket, "create_connection", deny_socket):
                                response = client.post("/api/tutor/stream", json={"session_id": session, "user_id": owner,
                                    "message": MESSAGE, "subject": "calculus", "mode": "socratic", "learning_context": ref.model_dump()})
                        messages = repository.list_messages(session)
                        saved = messages[-1] if messages else {}
                        meta = saved.get("learning_meta", {})
                        completed = response.status_code == 200 and "event: done" in response.text and "event: error" not in response.text
                        if not completed or len(inputs) != 1 or saved.get("role") != "assistant":
                            raise ValueError("application pair did not deliver exactly one fixed teacher response")
                        records.append({"case_id": case["id"], "arm": arm, "evidence_source": "fixed_fixture",
                            "case_sha256": sha(case), "case_rubric_sha256": sha(next(row for row in rubric["cases"] if row["id"] == case["id"])),
                            "student_claim": case["student_claim"], "user_message": MESSAGE,
                            "model_input": inputs[0], "model_input_sha256": sha(inputs[0]),
                            "response_sha256": sha(saved["content"]), "http_status": response.status_code,
                            "fixture_duration_seconds": round(time.monotonic() - started, 3),
                            "model_calls": calls, "provider_http_requests": 0, "usage": None,
                            "model_label": "fixed_fixture", "prompt_version": runtime(inputs[0])["prompt_version"],
                            "fresh_state": clean, "saved_user_turns": sum(row["role"] == "user" for row in messages),
                            "grade_boundary": meta.get("verified") is False and meta.get("is_correct") is None and meta.get("mastery_delta") == 0,
                            "mastery_writes": len(repository.list_mastery(owner)), "mistake_writes": len(repository.list_user_mistakes(owner))})
                    finally:
                        course.store.close()
    pairs = [{"case_id": case["id"], "only_exact_check_differs": pair_matches(
        next(row["model_input"] for row in records if row["case_id"] == case["id"] and row["arm"] == "D0"),
        next(row["model_input"] for row in records if row["case_id"] == case["id"] and row["arm"] == "D1"))} for case in cases]
    passed = all(pair["only_exact_check_differs"] for pair in pairs) and all(
        row["fresh_state"] and row["grade_boundary"] and row["saved_user_turns"] == 1
        and row["mastery_writes"] == row["mistake_writes"] == 0 for row in records)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, timeout=10)
    report = {"version": "r2-application-pairs-offline-v1", "engineering_passed": passed,
        "capture_git_sha": revision.stdout.strip() if revision.returncode == 0 else None,
        "capture_worktree_dirty": bool(dirty.stdout.strip()),
        "scope": "real in-process ASGI/SSE, compiled workflow, fixed model, synthetic principal, temp databases; no JWT or live model",
        "intervention": "harness removes exact_check at server context resolution in D0; production files unchanged",
        "quality_scored_runs": 0, "human_gold": "pending", "pairs": pairs, "records": records,
        "not_run": [{"case_id": case, "reason": "single-factor application contrast not established"} for case in ("L01", "L02", "T01", "T04")],
        "material_sha256": digest(CASES), "rubric_sha256": digest(RUBRIC), "source_sha256": {path.relative_to(ROOT).as_posix(): digest(path)
            for path in sorted((ROOT / "apps/api/app").rglob("*.py"))}, "capture_script_sha256": digest(Path(__file__))}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "results/r2-application-pairs.json")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == CASES.resolve() or output == Path(__file__).resolve() or (ROOT / "results").resolve() not in output.parents:
        parser.error("capture output must be inside the ignored results directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.worker:
        worker(output)
        return 0
    env = {key: value for key, value in os.environ.items() if "KEY" not in key and "TOKEN" not in key}
    env.update(LUOJIA_NO_DOTENV="1", PYTHONUTF8="1")
    with tempfile.TemporaryDirectory(prefix="r2-capture-output-", dir=ROOT / "results") as folder:
        temporary = Path(folder) / "capture.json"
        try:
            process = subprocess.run([sys.executable, str(Path(__file__)), "--offline", "--worker", "--output", str(temporary)],
                cwd=ROOT, env=env, capture_output=True, timeout=90)
        except subprocess.TimeoutExpired:
            print("R2 application capture timed out; no quality conclusion", file=sys.stderr)
            return 2
        if process.returncode or not temporary.exists():
            print("R2 application capture failed; no quality conclusion", file=sys.stderr)
            return 2
        report = load_json(temporary)
        output.write_bytes(temporary.read_bytes())
    print(f"R2 application pairs: {len(report['pairs'])} pairs, engineering_passed={report['engineering_passed']}; quality_scored_runs=0")
    return 0 if report["engineering_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
