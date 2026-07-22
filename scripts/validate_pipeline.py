#!/usr/bin/env python
import sys
import os

# Add apps/api to path if executed standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/api")))

from app.knowledge.pipeline.validator import validate_pipeline_output, KnowledgeRelation, KnowledgeUnit, SourceDocument


if __name__ == "__main__":
    print("Pipeline validation engine initialized.")

