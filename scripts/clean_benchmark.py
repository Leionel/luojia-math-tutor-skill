import json
import os

input_paths = [
    "data/LuojiaMathBench_v2.jsonl",
    r"C:\Users\Administrator\.gemini\antigravity-cli\brain\b4a42fa5-21cc-441b-8a2d-b00b1ecaf106\LuojiaMathBench_v2.jsonl"
]

input_path = None
for p in input_paths:
    if os.path.exists(p):
        input_path = p
        print(f"Using input file: {input_path}")
        break

if not input_path:
    raise FileNotFoundError("Could not find input file")

# Ensure directories exist
os.makedirs("results", exist_ok=True)
os.makedirs("data", exist_ok=True)

data = {} # id -> row

with open(input_path, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        row = json.loads(line)
        row_id = row.get("id")
        data[row_id] = row  # Keeps the last one encountered

evaluations = []
cleaned_data = []

keywords = ["矩阵", "行列式", "特征值", "积分", "极大似然", "方程", "求导", "分布"]

for row_id, row in data.items():
    # Extract evaluation
    if "evaluation" in row:
        eval_data = row.pop("evaluation")
        evaluations.append({
            "id": row_id,
            "model": "v7_baseline",
            "evaluation": eval_data
        })
    
    concept = row.get("concept", "")
    question = row.get("question", "")
    
    # Check keywords for tool_required
    needs_tool = False
    for kw in keywords:
        if kw in concept or kw in question:
            needs_tool = True
            break
            
    row["tool_required"] = needs_tool
    
    # Inject learning_objective
    row["learning_objective"] = f"深刻理解和掌握{concept}的核心原理与应用"
    
    # Inject student_profile
    row["student_profile"] = {
        "mastery_level": "low",
        "recent_errors": [concept]
    }
    
    cleaned_data.append(row)

with open("results/v7_baseline.jsonl", "w", encoding='utf-8') as f:
    for e in evaluations:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

with open("data/LuojiaMathBench_v8.jsonl", "w", encoding='utf-8') as f:
    for row in cleaned_data:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"Done processing. Kept {len(cleaned_data)} rows. Extracted {len(evaluations)} evaluations.")
