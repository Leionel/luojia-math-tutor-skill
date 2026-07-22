#!/usr/bin/env python
import argparse
import dataclasses
import json
import os
import sys

# Ensure apps/api is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/api")))

from app.knowledge.pipeline.ingest import create_source_document


def main():
    parser = argparse.ArgumentParser(description="Ingest document and create SourceDocument metadata.")
    parser.add_argument("file_path", type=str, help="Path to document file")
    parser.add_argument("--course-id", type=str, default="default_course", help="Course ID")
    parser.add_argument("--owner-id", type=str, default="system", help="Owner ID")

    args = parser.parse_args()

    doc = create_source_document(
        file_path=args.file_path,
        course_id=args.course_id,
        owner_id=args.owner_id,
    )

    print(json.dumps(dataclasses.asdict(doc), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
