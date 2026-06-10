import json
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
results_file = os.path.join(project_root, "data", "LuojiaMathBench_Eval_Results.jsonl")

if not os.path.exists(results_file):
    print("No evaluation results found yet.")
    exit(0)

results = []
with open(results_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass

if not results:
    print("No valid evaluation results found yet.")
    exit(0)

total = len(results)
passed = sum(1 for r in results if r["evaluation"].get("passed", False))

direct_answer_leak_fails = sum(1 for r in results if r["evaluation"].get("direct_answer_leak", False))
sympy_verifiable_fails = sum(1 for r in results if not r["evaluation"].get("sympy_verifiable", True))
action_aligned_fails = sum(1 for r in results if not r["evaluation"].get("action_aligned", True))

print(f"Total Evaluated: {total}")
print(f"Passed: {passed} ({(passed/total)*100:.1f}%)")
print(f"Failed due to Direct Answer Leak: {direct_answer_leak_fails} ({(direct_answer_leak_fails/total)*100:.1f}%)")
print(f"Failed due to Sympy Format issues: {sympy_verifiable_fails} ({(sympy_verifiable_fails/total)*100:.1f}%)")
print(f"Failed due to Unaligned Action: {action_aligned_fails} ({(action_aligned_fails/total)*100:.1f}%)")

print("\n--- Failed Examples ---")
for r in results[:10]:
    if not r["evaluation"].get("passed", False):
        print(f"\nID: {r['id']}")
        print(f"Reason: {r['evaluation'].get('reason')}")
        print(f"Suggested Fix: {r['evaluation'].get('suggested_fix')}")
