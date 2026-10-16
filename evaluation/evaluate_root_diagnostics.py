"""Offline engineering replay, separate from teacher gold and retrieval benchmarks."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ["LUOJIA_NO_DOTENV"] = "1"
for key in ("LLM_API_KEY", "MINERU_API_KEY", "TAVILY_API_KEY", "DASHSCOPE_API_KEY"):
    os.environ.pop(key, None)
sys.path.insert(0, str(ROOT / "apps/api"))
from app.knowledge.course_service import CourseService
from app.knowledge.course_store import CourseStore
from app.tutor.root_diagnostics import RootEpisodeService, RootSubmission


def evaluate():
    fixture = ROOT / "evaluation/root_diagnostic_episodes.json"
    results = []
    for item in json.loads(fixture.read_text(encoding="utf-8"))["episodes"]:
        service = RootEpisodeService(CourseService(store=CourseStore()))
        def submit(data, identity, episode=None):
            return service.submit("fixture-user", "fixture-session", RootSubmission(attempt=data, attempt_id=identity, episode_id=episode))
        def ack(report):
            return service.acknowledge("fixture-user", "fixture-session", report["episode_id"], report["attempt_id"], report["feedback_id"])
        error = submit(item["attempt"], "error")
        ack(error)
        revision = submit(item["revision"], "revision", error["episode_id"])
        outcome = ack(revision)["outcome"]
        control = submit(item["legal_control"], "control")
        control_outcome = ack(control)["outcome"]
        passed = (error["family"] == item["family"] and error["status"] == item["expected_status"]
                  and revision["complete"] and outcome == "assisted_success"
                  and control["complete"] and control_outcome == "observed_success")
        results.append(dict(id=item["id"], family=error["family"], status=error["status"],
                            case_id=error["case_id"], error_step=error["error_step"],
                            revision_outcome=outcome, control_outcome=control_outcome, passed=passed))
    return dict(scope="engineering fixtures only", oracle_version="root-oracle-v1",
                tolerance_version="root-tolerance-v1", teacher_review="pending", unseen_evaluation="not_run",
                fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                families=len({r["family"] for r in results}), passed=sum(r["passed"] for r in results),
                total=len(results), episodes=results)


if __name__ == "__main__":
    report = evaluate()
    destination = ROOT / "results/root_diagnostics_eval.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['passed']}/{report['total']} triplets; {report['families']} families; teacher review pending")
    raise SystemExit(0 if report["passed"] == report["total"] else 1)
