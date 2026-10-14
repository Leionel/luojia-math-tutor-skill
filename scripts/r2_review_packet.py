"""Build or check an unsigned R2 mathematics/content review packet.

Reads source literals and public development JSON only. It never imports the app,
executes student code, opens a database, sends HTTP, or assigns quality scores.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

from s5_content import validate_content
from s5_quality import digest, load_json

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "evaluation/r1/a0-development-cases.json",
    "evaluation/s5/manifest.json",
    "evaluation/s5/development-content-v1.json",
    "evaluation/r2/b4-variants-v1.json",
    "apps/api/app/tutor/learning_workspace.py",
    "apps/api/app/tutor/learning_extensions.py",
)


def canonical_digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def source_literal(path: Path, name: str):
    """Read a top-level literal without importing production code."""
    matches = []
    for node in ast.parse(path.read_text(encoding="utf-8-sig")).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            matches.append(ast.literal_eval(node.value))
    if len(matches) != 1:
        raise ValueError(f"expected one literal {name}")
    return matches[0]


def make_item(item_id: str, source: str, material: dict, review_focus: str) -> dict:
    return {
        "id": item_id,
        "source": source,
        "material": material,
        "material_sha256": canonical_digest(material),
        "review_focus": review_focus,
        "author_review": {"status": "pending", "reviewer": None, "date": None, "notes": None},
        "independent_human_review": {"status": "pending", "reviewer": None, "date": None, "notes": None},
    }


def build_packet() -> dict:
    paths = {name: ROOT / name for name in SOURCES}
    a0 = load_json(paths["evaluation/r1/a0-development-cases.json"])
    if a0.get("status") != "agent_prepared_only" or len(a0.get("cases", [])) != 16:
        raise ValueError("R1 development set changed; review the split before regenerating")
    manifest_path = paths["evaluation/s5/manifest.json"]
    s5 = validate_content(manifest_path)
    if s5 is None or len(s5["cases"]) != 8:
        raise ValueError("S5 bound content is unavailable")
    workspace = paths["apps/api/app/tutor/learning_workspace.py"]
    cards = source_literal(workspace, "CARDS")
    questions = source_literal(workspace, "QUESTIONS")
    rubrics = source_literal(workspace, "ASSESSMENT_RUBRICS")
    if len(cards) != 4 or len(questions) != 6 or {row[0] for row in questions} != set(rubrics):
        raise ValueError("B2/B3 content shape changed; review the packet builder")
    extensions = paths["apps/api/app/tutor/learning_extensions.py"]
    assignment_id = source_literal(extensions, "ASSIGNMENT_ID")
    static_rule_version = source_literal(extensions, "STATIC_RULE_VERSION")
    variants = load_json(paths["evaluation/r2/b4-variants-v1.json"])
    if (variants.get("version") != "r2-b4-public-development-v1"
            or variants.get("status") != "agent_prepared_only"
            or variants.get("assignment_id") != assignment_id
            or len(variants.get("cases", [])) != 4):
        raise ValueError("B4 variants or assignment changed")

    items = []
    for case in a0["cases"]:
        material = {key: case[key] for key in ("domain", "kind", "student_claim", "independent_basis", "expected_boundary")}
        items.append(make_item(f"A0-{case['id']}", "evaluation/r1/a0-development-cases.json", material,
                               "Check the mathematics, quantifiers, allowed alternatives and teaching boundary."))
    for case in s5["cases"]:
        material = {key: case[key] for key in ("prompt", "independent_solution", "rubric", "input_sha256", "rubric_sha256")}
        items.append(make_item(f"S5-{case['id']}", "evaluation/s5/development-content-v1.json", material,
                               "Check the independent derivation and each required/forbidden rubric item."))
    for card_id, card in sorted(cards.items()):
        if not 0 <= card["answer"] < len(card["options"]):
            raise ValueError("B2 answer index invalid")
        items.append(make_item(f"B2-{card_id}", "apps/api/app/tutor/learning_workspace.py:CARDS", card,
                               "Check conditions, counterexample, answer and course excerpt separately; the graph excerpt is not in this packet."))
    for row in questions:
        key, prompt, options, answer, explanation, unit_id = row
        if key not in rubrics or not 0 <= answer < len(options) or unit_id not in cards:
            raise ValueError("B3 question/rubric linkage invalid")
        material = {"question_id": key, "prompt": prompt, "options": options,
                    "reference_answer_index": answer, "explanation": explanation,
                    "unit_id": unit_id, "layered_rubric": rubrics[key]}
        items.append(make_item(f"B3-{key}", "apps/api/app/tutor/learning_workspace.py:QUESTIONS/ASSESSMENT_RUBRICS",
                               material, "Check reference answer, assumptions, feedback wording and every distractor without inferring student error cause."))
    for case in variants["cases"]:
        if not isinstance(case.get("code"), str) or len(case["code"]) > 4000:
            raise ValueError("B4 public code variant invalid")
        ast.parse(case["code"])  # syntax only; never execute the student's code
        material = {"assignment_id": assignment_id, "static_rule_version": static_rule_version,
                    "scope": variants["scope"], "code": case["code"], "review_question": case["review_question"]}
        items.append(make_item(case["id"], "evaluation/r2/b4-variants-v1.json", material,
                               "Blindly judge mathematical validity and whether each static hint could mislead; a hint is not a verdict."))
    ids = [item["id"] for item in items]
    if len(ids) != 38 or len(ids) != len(set(ids)):
        raise ValueError("unexpected or duplicate review items")
    return {
        "version": "r2-unsigned-review-packet-v1",
        "status": "agent_prepared_only_human_reviews_pending",
        "source_sha256": {name: digest(path) for name, path in paths.items()},
        "item_counts": {"a0": 16, "s5": 8, "b2": 4, "b3": 6, "b4": 4},
        "meaning": "38 source items for content review; overlapping topics are not 38 independent quality trials or a scored denominator.",
        "items": items,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/r2/review-packet-v1.json")
    parser.add_argument("--check", action="store_true", help="fail if the saved packet is missing or stale")
    args = parser.parse_args(argv)
    try:
        packet = build_packet()
        output = args.output.resolve()
        if output in {(ROOT / name).resolve() for name in SOURCES}:
            raise ValueError("cannot overwrite a source file")
        if args.check:
            if load_json(output) != packet:
                raise ValueError("saved review packet is stale or altered")
        else:
            if output.exists() and load_json(output) != packet:
                raise ValueError("existing packet differs; version it instead of overwriting")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("R2 unsigned review packet: 38 bound items; human review remains pending")
        return 0
    except (OSError, ValueError, SyntaxError, KeyError, TypeError) as exc:
        print(f"R2 packet rejected: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
