from collections import defaultdict, deque
import json
import logging
from pathlib import Path
from typing import Any, Optional

from app.knowledge.schema import KnowledgeUnit, KnowledgeRelation
from app.knowledge.boundary import BoundaryChecker, BoundaryPolicy, ScopeLevel
from app.knowledge.case_schema import TeachingCase
from app.knowledge.case_repository import TeachingCaseRepository

logger = logging.getLogger(__name__)

# Task-type specific relation filter
TASK_TYPE_RELATIONS = {
    "concept_explanation": {
        "prerequisite_of", "part_of", "special_case_of", "example_of", "similar_to", "prereq"
    },
    "convergence_analysis": {
        "converges_if", "requires", "counterexample_of", "has_error_bound", "prerequisite_of"
    },
    "derivation": {
        "derives_from", "supports_proof", "requires", "prerequisite_of"
    },
    "code_task": {
        "implemented_by", "uses_stopping_rule", "common_mistake_of", "exercise_of"
    },
    "error_debugging": {
        "misconception_of", "counterexample_of", "common_mistake_of", "remediated_by"
    }
}


class CourseGraphRepository:
    """Canonical Course Graph Repository supporting typed relations, boundary checking, and React Flow export."""

    def __init__(self, course_id: str = "numerical_analysis"):
        self.course_id = course_id
        self.units: dict[str, KnowledgeUnit] = {}
        self.relations: list[KnowledgeRelation] = []
        self.boundary_checker = BoundaryChecker()
        self.case_repo = TeachingCaseRepository()
        self._out_edges: dict[str, list[KnowledgeRelation]] = defaultdict(list)
        self._in_edges: dict[str, list[KnowledgeRelation]] = defaultdict(list)

    def add_unit(self, unit: KnowledgeUnit, boundary: Optional[BoundaryPolicy] = None) -> None:
        self.units[unit.id] = unit
        if boundary:
            self.boundary_checker.set_policy(boundary)
        elif unit.id not in self.boundary_checker.policies:
            # Derive default boundary from unit teaching_role
            scope = ScopeLevel.CORE.value
            if unit.teaching_role == "auxiliary":
                scope = ScopeLevel.PREREQUISITE.value
            elif unit.teaching_role == "extension":
                scope = ScopeLevel.EXTENSION.value
            self.boundary_checker.set_policy(
                BoundaryPolicy(course_id=self.course_id, unit_id=unit.id, scope_level=scope)
            )

    def add_relation(self, relation: KnowledgeRelation) -> None:
        self.relations.append(relation)
        self._out_edges[relation.source_unit_id].append(relation)
        self._in_edges[relation.target_unit_id].append(relation)

    def add_case(self, case: TeachingCase) -> None:
        self.case_repo.add_case(case)

    def get_unit(self, unit_id: str) -> Optional[KnowledgeUnit]:
        return self.units.get(unit_id)

    def get_subgraph(
        self,
        center_unit_ids: list[str],
        max_depth: int = 1,
        task_mode: Optional[str] = None,
        allow_extension: bool = True
    ) -> tuple[list[KnowledgeUnit], list[KnowledgeRelation]]:
        """Extract boundary-constrained, relation-aware subgraph around center_unit_ids."""
        visited_units = set(center_unit_ids)
        collected_relations = []
        queue = deque([(uid, 0) for uid in center_unit_ids if uid in self.units])

        allowed_rel_types = TASK_TYPE_RELATIONS.get(task_mode) if task_mode else None

        while queue:
            curr_id, curr_depth = queue.popleft()
            if curr_depth >= max_depth:
                continue

            # Check boundary before expanding from this node
            can_expand, _ = self.boundary_checker.can_expand(
                curr_id, curr_depth, task_mode=task_mode or "concept_explanation", allow_extension=allow_extension
            )
            if not can_expand:
                continue

            # Search outgoing and incoming edges
            all_neighbors = []
            for r in self._out_edges.get(curr_id, []):
                if allowed_rel_types and r.relation_type not in allowed_rel_types:
                    continue
                all_neighbors.append((r.target_unit_id, r))

            for r in self._in_edges.get(curr_id, []):
                if allowed_rel_types and r.relation_type not in allowed_rel_types:
                    continue
                all_neighbors.append((r.source_unit_id, r))

            for neighbor_id, rel in all_neighbors:
                # Boundary check target node
                target_scope = self.boundary_checker.get_scope_level(neighbor_id)
                if target_scope == ScopeLevel.EXTERNAL:
                    continue
                if target_scope == ScopeLevel.EXTENSION and not allow_extension:
                    continue

                if rel not in collected_relations:
                    collected_relations.append(rel)

                if neighbor_id not in visited_units and neighbor_id in self.units:
                    visited_units.add(neighbor_id)
                    queue.append((neighbor_id, curr_depth + 1))

        return [self.units[uid] for uid in visited_units if uid in self.units], collected_relations

    def export_react_flow(
        self,
        student_overlay: Optional[dict[str, Any]] = None,
        scope_filter: Optional[str] = None
    ) -> dict[str, Any]:
        """Export graph to React Flow { nodes, edges } structure."""
        nodes = []
        unit_states = (student_overlay or {}).get("units", {})

        # Arrange nodes by scope/difficulty level
        levels = defaultdict(list)
        for unit in self.units.values():
            scope = self.boundary_checker.get_scope_level(unit.id).value
            if scope_filter and scope != scope_filter:
                continue
            levels[unit.difficulty].append(unit)

        y_offset = 60
        for diff in sorted(levels.keys()):
            row_units = levels[diff]
            x_start = 100
            spacing = 260
            for idx, unit in enumerate(row_units):
                scope = self.boundary_checker.get_scope_level(unit.id).value
                state = unit_states.get(unit.id, {})
                mastery = state.get("mastery_estimate", 0.5)

                if mastery >= 0.8:
                    status = "mastered"
                elif mastery >= 0.3:
                    status = "learning"
                else:
                    status = "locked"

                nodes.append({
                    "id": unit.id,
                    "position": {"x": x_start + idx * spacing, "y": y_offset},
                    "type": "skillNode",
                    "data": {
                        "label": unit.title,
                        "status": status,
                        "unit_type": unit.type,
                        "scope": scope,
                        "difficulty": unit.difficulty,
                        "mastery": mastery,
                        "description": unit.content[:80] + ("..." if len(unit.content) > 80 else ""),
                    },
                })
            y_offset += 140

        visible_node_ids = {n["id"] for n in nodes}
        edges = []
        for idx, r in enumerate(self.relations):
            if r.source_unit_id in visible_node_ids and r.target_unit_id in visible_node_ids:
                is_prereq = r.relation_type in ("prerequisite_of", "prereq", "requires")
                edges.append({
                    "id": f"e_{r.source_unit_id}_{r.target_unit_id}_{idx}",
                    "source": r.source_unit_id,
                    "target": r.target_unit_id,
                    "label": r.relation_type,
                    "animated": is_prereq,
                    "style": {
                        "stroke": "#3b82f6" if is_prereq else "#9ca3af",
                        "strokeWidth": 2 if is_prereq else 1,
                    },
                })

        return {"nodes": nodes, "edges": edges, "total_nodes": len(nodes), "total_edges": len(edges)}

    def load_from_course_pack(self, course_pack_data: dict[str, Any]) -> None:
        """Load course pack containing units, relations, boundaries, and cases."""
        self.course_id = course_pack_data.get("course_id", self.course_id)

        # 1. Load boundaries
        for b_dict in course_pack_data.get("boundaries", []):
            policy = BoundaryPolicy.from_dict(b_dict)
            self.boundary_checker.set_policy(policy)

        # 2. Load units
        for u_dict in course_pack_data.get("units", []):
            unit = KnowledgeUnit(
                id=u_dict["id"],
                course_id=self.course_id,
                title=u_dict.get("title", ""),
                type=u_dict.get("type", "concept"),
                content=u_dict.get("content", ""),
                latex=u_dict.get("latex", ""),
                intuitive_explanation=u_dict.get("intuitive_explanation", ""),
                solution=u_dict.get("solution", ""),
                keywords=u_dict.get("keywords", []),
                aliases=u_dict.get("aliases", []),
                difficulty=int(u_dict.get("difficulty", 3)),
                teaching_role=u_dict.get("teaching_role", "core"),
                provenance=u_dict.get("provenance", "curated"),
                review_status=u_dict.get("review_status", "verified"),
            )
            boundary = self.boundary_checker.get_policy(unit.id)
            self.add_unit(unit, boundary=boundary)

        # 3. Load relations
        for r_dict in course_pack_data.get("relations", []):
            rel = KnowledgeRelation(
                source_unit_id=r_dict["source_unit_id"],
                target_unit_id=r_dict["target_unit_id"],
                relation_type=r_dict["relation_type"],
                confidence=float(r_dict.get("confidence", 1.0)),
                provenance=r_dict.get("provenance", "rule"),
                review_status=r_dict.get("review_status", "verified"),
            )
            self.add_relation(rel)

        # 4. Load teaching cases
        for c_dict in course_pack_data.get("teaching_cases", []):
            case = TeachingCase.from_dict(c_dict)
            self.add_case(case)

        logger.info(
            f"Loaded course pack for {self.course_id}: {len(self.units)} units, "
            f"{len(self.relations)} relations, {self.case_repo.count()} teaching cases."
        )
