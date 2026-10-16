import json
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
results_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(project_root, "results", "v8_eval_results.jsonl")

if not os.path.exists(results_file):
    print(f"No evaluation results found: {results_file}")
    exit(0)

results = []
with open(results_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass

errors = [r for r in results if r.get("error")]
scored = [r for r in results if not r.get("error") and r.get("evaluation")]

total = len(scored)
if not total:
    print(f"No scored results in {results_file} ({len(errors)} unscored errors).")
    exit(0)

passed = sum(1 for r in scored if r["evaluation"].get("passed", False))
direct_answer_leak_fails = sum(1 for r in scored if r["evaluation"].get("direct_answer_leak", False))
sympy_verifiable_fails = sum(1 for r in scored if not r["evaluation"].get("sympy_verifiable", True))
action_aligned_fails = sum(1 for r in scored if not r["evaluation"].get("action_aligned", True))

print(f"Results file: {results_file}")
print(f"Total lines: {len(results)} ({len(errors)} unscored errors, {total} scored)")
print(f"Passed: {passed} ({(passed/total)*100:.1f}%)")
print(f"Direct Answer Leak: {direct_answer_leak_fails} ({(direct_answer_leak_fails/total)*100:.1f}%)")
print(f"Sympy Format issues: {sympy_verifiable_fails} ({(sympy_verifiable_fails/total)*100:.1f}%)")
print(f"Unaligned Action: {action_aligned_fails} ({(action_aligned_fails/total)*100:.1f}%)")

print("\n--- Failed Examples ---")
for r in scored:
    if not r["evaluation"].get("passed", False):
        print(f"\nID: {r['id']}")
        print(f"Reason: {r['evaluation'].get('reason')}")
        print(f"Suggested Fix: {r['evaluation'].get('suggested_fix')}")
