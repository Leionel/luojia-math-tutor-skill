import dataclasses
import json
from pathlib import Path

from app.knowledge.pipeline.ingest import create_source_document
from app.knowledge.pipeline.extractor import extract_units_from_markdown
from app.knowledge.pipeline.relations import generate_candidate_relations
from app.knowledge.pipeline.validator import validate_pipeline_output


def run_pipeline(input_path: Path, output_path: Path, course_id: str = "linear_algebra_101"):
    """Run full M1 pipeline: Ingest -> Extract -> Relation -> Validate -> Export."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # 1. Ingest
    doc = create_source_document(input_path, course_id=course_id)

    # 2. Extract units
    content = input_path.read_text(encoding="utf-8")
    units = extract_units_from_markdown(content, source_document_id=doc.id, course_id=course_id)

    # 3. Generate candidate relations
    relations = generate_candidate_relations(units)

    # 4. Validate
    is_valid, errors = validate_pipeline_output(doc, units, relations)
    if not is_valid:
        raise ValueError(f"Pipeline validation failed: {errors}")

    # 5. Export
    output_data = {
        "document": dataclasses.asdict(doc),
        "units": [dataclasses.asdict(u) for u in units],
        "relations": [dataclasses.asdict(r) for r in relations],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_data
