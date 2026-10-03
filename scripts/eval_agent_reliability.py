"""Versioned offline contract evaluation; executes production-bound regression fixtures.

This is not a model-quality benchmark. Parameterized instances are the denominator;
missing, skipped, duplicate, unexpected or failing instances fail the evaluation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(manifest, xml):
    cases = manifest["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("empty or duplicate case manifest")
    selectors = {c["selector"] for c in cases}
    if len(selectors) != len(cases):
        raise ValueError("duplicate selector")
    buckets = {c["id"]: [] for c in cases}
    seen = set()
    for item in ET.fromstring(xml).iter("testcase"):
        key = (item.get("classname"), item.get("name"))
        if key in seen:
            raise ValueError("duplicate test instance")
        seen.add(key)
        matches = [c for c in cases if
                   Path(c["selector"].split("::")[0]).stem == (key[0] or "").split(".")[-1]
                   and c["selector"].split("::")[1] == (key[1] or "").split("[")[0]]
        if len(matches) != 1:
            raise ValueError("unexpected test instance")
        buckets[matches[0]["id"]].append({"name": key[1], "passed":
            not any(item.find(tag) is not None for tag in ("failure", "error", "skipped"))})
    results = []
    for case in cases:
        instances = buckets[case["id"]]
        expected = case["expected_instances"]
        if type(expected) is not int or expected < 1:
            raise ValueError("invalid expected denominator")
        passed = sum(i["passed"] for i in instances)
        results.append({**case, "passed_instances": passed, "observed_instances": len(instances),
                        "passed": len(instances) == expected and passed == expected,
                        "failed_instances": [i["name"] for i in instances if not i["passed"]]})
    return {"cases": results, "passed_contracts": sum(c["passed"] for c in results),
            "expected_contracts": len(cases), "passed_instances": sum(c["passed_instances"] for c in results),
            "expected_instances": sum(c["expected_instances"] for c in cases),
            "passed": all(c["passed"] for c in results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/agent-reliability.json")
    args = parser.parse_args()
    manifest_path = ROOT / "evaluation/agent_reliability_v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    env = {k: v for k, v in os.environ.items() if not k.endswith("API_KEY")}
    env.update(LUOJIA_NO_DOTENV="1", PYTHONUTF8="1", PYTEST_ADDOPTS="")
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="luojia-eval-") as temp:
        junit = Path(temp) / "results.xml"
        command = [sys.executable, "-m", "pytest", "-q", "-o", "addopts=", "--junitxml", str(junit),
                   *[c["selector"] for c in manifest["cases"]]]
        try:
            process = subprocess.run(command, cwd=ROOT / "apps/api", env=env,
                                     capture_output=True, timeout=180)
            if not junit.exists():
                raise ValueError("pytest produced no report")
            summary = summarize(manifest, junit.read_text(encoding="utf-8"))
            summary["passed"] = summary["passed"] and process.returncode == 0
            summary["runner_exit_code"] = process.returncode
        except (ValueError, ET.ParseError, subprocess.TimeoutExpired) as exc:
            summary = {"passed": False, "runner_error": type(exc).__name__}
    sources = sorted([* (ROOT / "apps/api/app").rglob("*.py"),
                      * (ROOT / "apps/api/tests").glob("*.py"), Path(__file__)])
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"],
                           cwd=ROOT, capture_output=True, text=True)
    report = {"version": manifest["version"], "scope": manifest["scope"],
              "git_sha": git.stdout.strip() if git.returncode == 0 else None,
              "tracked_worktree_dirty": bool(dirty.stdout.strip()), "python": sys.version.split()[0],
              "command": "python scripts/eval_agent_reliability.py", "duration_seconds": round(time.monotonic()-started, 3),
              "manifest_sha256": digest(manifest_path),
              "source_sha256": {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}, **summary}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Offline protocol contracts: {report.get('passed_contracts', 0)}/{report.get('expected_contracts', len(manifest['cases']))}; "
          f"instances: {report.get('passed_instances', 0)}/{report.get('expected_instances', 0)}; passed={report['passed']}")
    print(f"Report: {args.output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
