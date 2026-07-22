import re
from app.knowledge.schema import KnowledgeRelation, KnowledgeUnit


def generate_candidate_relations(units: list[KnowledgeUnit]) -> list[KnowledgeRelation]:
    """
    Generate candidate KnowledgeRelation edges between KnowledgeUnits using title matching and text references.
    """
    relations: list[KnowledgeRelation] = []
    unit_map = {unit.id: unit for unit in units}
    title_to_id = {unit.title.strip(): unit.id for unit in units if unit.title}

    for unit in units:
        content = unit.content
        
        # 1. Check title mentions (e.g. "根据定义 5.1", "由定理 2 可知")
        for target_title, target_id in title_to_id.items():
            if target_id == unit.id:
                continue
            if len(target_title) >= 3 and target_title in content:
                rel_type = "prerequisite"
                if unit.type == "证明" and unit_map[target_id].type == "定理":
                    rel_type = "supports_proof"
                elif unit.type == "例题" or unit.type == "习题":
                    rel_type = "example_of" if unit.type == "例题" else "exercise_of"

                relations.append(
                    KnowledgeRelation(
                        source_unit_id=target_id,
                        target_unit_id=unit.id,
                        relation_type=rel_type,
                        confidence=0.85,
                        provenance="rule",
                        review_status="draft",
                    )
                )

        # 2. Sequential prerequisite fallback within the same section for definitions -> theorems
        # (handy heuristic for textbooks)

    return relations
