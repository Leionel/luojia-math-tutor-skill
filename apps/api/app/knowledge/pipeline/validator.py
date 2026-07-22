from app.knowledge.schema import KnowledgeRelation, KnowledgeUnit, SourceDocument


def validate_pipeline_output(
    doc: SourceDocument,
    units: list[KnowledgeUnit],
    relations: list[KnowledgeRelation],
) -> tuple[bool, list[str]]:
    """
    Validate Schema v1 data contracts and integrity for pipeline output.
    Returns (is_valid, errors).
    """
    errors: list[str] = []

    # 1. Document validation
    if not doc.id or not doc.filename:
        errors.append("SourceDocument missing id or filename")

    # 2. Units validation
    unit_ids = set()
    for idx, u in enumerate(units):
        if not u.id:
            errors.append(f"Unit #{idx} missing id")
        elif u.id in unit_ids:
            errors.append(f"Duplicate Unit ID found: {u.id}")
        else:
            unit_ids.add(u.id)

        if not u.title and not u.content:
            errors.append(f"Unit {u.id} has empty title and content")

        if u.page_start is not None and u.page_end is not None:
            if u.page_start > u.page_end:
                errors.append(f"Unit {u.id} page_start ({u.page_start}) > page_end ({u.page_end})")

    # 3. Relations validation
    for idx, r in enumerate(relations):
        if r.source_unit_id not in unit_ids:
            errors.append(f"Relation #{idx} source_unit_id ({r.source_unit_id}) not found in units")
        if r.target_unit_id not in unit_ids:
            errors.append(f"Relation #{idx} target_unit_id ({r.target_unit_id}) not found in units")

    return len(errors) == 0, errors
