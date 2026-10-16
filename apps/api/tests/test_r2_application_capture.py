"""Application pair capture validates an intervention, not model mathematics."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from r2_application_capture import pair_matches


def test_application_pairs_do_not_promote_fixed_responses_to_quality():
    (ROOT / "results").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="r2-pair-test-", dir=ROOT / "results") as folder:
        output = Path(folder) / "capture.json"
        process = subprocess.run([sys.executable, str(ROOT / "scripts/r2_application_capture.py"),
            "--offline", "--output", str(output)], cwd=ROOT, capture_output=True, text=True, timeout=100)
        assert process.returncode == 0, process.stderr
        report = json.loads(output.read_text(encoding="utf-8"))
    assert report["engineering_passed"] is True
    assert report["quality_scored_runs"] == 0 and report["human_gold"] == "pending"
    assert len(report["records"]) == 4 and len(report["not_run"]) == 4
    assert all(row["fresh_state"] and row["saved_user_turns"] == 1 and row["grade_boundary"] for row in report["records"])
    assert all(row["provider_http_requests"] == 0 and row["usage"] is None for row in report["records"])
    assert all(row["mastery_writes"] == row["mistake_writes"] == 0 for row in report["records"])


def test_pair_rejects_an_extra_change_besides_exact_evidence():
    def messages(value):
        return [{"role": "system", "content": "same instructions"},
                {"role": "developer", "content": "[RUNTIME_CONTEXT]\n" + json.dumps(value) + "\n[/RUNTIME_CONTEXT]"},
                {"role": "developer", "content": "same output budget"},
                {"role": "user", "content": "same student request"}]
    d0 = {"intent": "check_student_step", "learning_task": {"student_claim": "correct step", "rows": [0, 1, 0]}}
    d1 = deepcopy(d0)
    d1["learning_task"]["exact_check"] = {"scope": "fixed case only"}
    assert pair_matches(messages(d0), messages(d1))
    d1["learning_task"]["student_claim"] = "different claim"
    assert not pair_matches(messages(d0), messages(d1))
    d1 = deepcopy(d0)
    d1["learning_task"]["exact_check"] = {"scope": "fixed case only"}
    changed = messages(d1)
    changed[0]["content"] = "different instructions"
    assert not pair_matches(messages(d0), changed)


def test_capture_cannot_overwrite_public_case_material():
    process = subprocess.run([sys.executable, str(ROOT / "scripts/r2_application_capture.py"), "--offline",
        "--output", str(ROOT / "evaluation/r1/a0-development-cases.json")], cwd=ROOT,
        capture_output=True, text=True, timeout=10)
    assert process.returncode == 2
    assert "ignored results directory" in process.stderr
