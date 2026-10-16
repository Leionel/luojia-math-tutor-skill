"""R2 content packet must stay unsigned and bound to the reviewed source."""
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/r2_review_packet.py"


def test_review_packet_is_current_unsigned_and_covers_each_source_family():
    process = subprocess.run([sys.executable, str(SCRIPT), "--check"], cwd=ROOT,
                             capture_output=True, text=True, timeout=20)
    assert process.returncode == 0, process.stderr
    packet = json.loads((ROOT / "evaluation/r2/review-packet-v1.json").read_text(encoding="utf-8"))
    assert packet["status"] == "agent_prepared_only_human_reviews_pending"
    assert packet["item_counts"] == {"a0": 16, "s5": 8, "b2": 4, "b3": 6, "b4": 4}
    assert all(item["independent_human_review"]["status"] == "pending" for item in packet["items"])
    assert all(item["author_review"]["reviewer"] is None for item in packet["items"])


def test_review_packet_check_rejects_changed_or_fake_signed_artifact(tmp_path):
    packet = json.loads((ROOT / "evaluation/r2/review-packet-v1.json").read_text(encoding="utf-8"))
    packet["items"][0]["independent_human_review"]["status"] = "approved"
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
    process = subprocess.run([sys.executable, str(SCRIPT), "--check", "--output", str(changed)], cwd=ROOT,
                             capture_output=True, text=True, timeout=20)
    assert process.returncode == 2
    assert "stale or altered" in process.stderr
