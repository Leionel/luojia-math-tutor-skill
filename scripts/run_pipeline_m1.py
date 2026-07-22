#!/usr/bin/env python
import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

# Ensure apps/api is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/api")))

from app.knowledge.pipeline.runner import run_pipeline


def main():
    repo_root = Path(__file__).resolve().parents[1]
    default_input = repo_root / "data" / "sample_linear_algebra_ch5.md"
    default_output = repo_root / "luojia-math-tutor" / "references" / "output" / "m1_linear_algebra_ch5_units.json"

    parser = argparse.ArgumentParser(description="Run M1 Knowledge Structuring Pipeline.")
    parser.add_argument("--input", type=Path, default=default_input, help="Input Markdown file path")
    parser.add_argument("--output", type=Path, default=default_output, help="Output JSON file path")
    parser.add_argument("--course-id", type=str, default="linear_algebra_101", help="Course ID")

    args = parser.parse_args()

    data = run_pipeline(args.input, args.output, course_id=args.course_id)
    print(f"Pipeline executed successfully!")
    print(f"Document ID: {data['document']['id']}")
    print(f"Knowledge Units Extracted: {len(data['units'])}")
    print(f"Knowledge Relations Generated: {len(data['relations'])}")
    print(f"Output saved to: {args.output}")


if __name__ == "__main__":
    main()
