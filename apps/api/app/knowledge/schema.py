from dataclasses import dataclass, field
from typing import Any


@dataclass
class KnowledgeItem:
    id: str
    subject: str
    source_file: str
    concept_zh: str
    prerequisite: list[str]
    description: str
    intuitive_explanation: str
    solution: str
    type: str = "concept"
    chapter: str = ""
    section: str = ""
    related_exercises: list[str] = field(default_factory=list)
    difficulty: int = 3
    source: dict[str, Any] = field(default_factory=dict)

    def to_unit(
        self,
        course_id: str = "default_course",
        prereq_id_map: dict[str, str] | None = None,
    ) -> "KnowledgeUnit":
        """Convert legacy KnowledgeItem to Schema v1 KnowledgeUnit."""
        prereq_id_map = prereq_id_map or {}
        prereq_refs = []
        for p in self.prerequisite:
            pid = prereq_id_map.get(p)
            prereq_refs.append({
                "unit_id": pid or "",
                "display_name": p
            })

        return KnowledgeUnit(
            id=self.id,
            course_id=course_id,
            schema_version="v1",
            type=self.type or "concept",
            title=self.concept_zh,
            content=self.description,
            intuitive_explanation=self.intuitive_explanation,
            solution=self.solution,
            source_document_id=self.source_file,
            keywords=[self.concept_zh],
            chapter_path=[self.chapter, self.section] if self.chapter or self.section else [],
            difficulty=self.difficulty,
            expected_prerequisites=prereq_refs,
            provenance="manual",
            review_status="verified",
        )


@dataclass
class KnowledgeHit:
    item: KnowledgeItem
    score: int


# ==========================================
# Schema v1 Data Contracts (课程知识数据契约)
# ==========================================

@dataclass
class SourceDocument:
    id: str
    course_id: str
    filename: str
    checksum: str = ""
    parser: str = "miner_u"
    parser_version: str = "1.0"
    page_count: int = 0
    language: str = "zh"
    owner_id: str = "system"
    access_scope: str = "course"  # public | course | private
    status: str = "active"  # uploaded | parsed | reviewed | active | deprecated
    created_at: str = ""


@dataclass
class KnowledgeUnit:
    id: str
    course_id: str
    schema_version: str = "v1"
    type: str = "concept"  # 定义 | 定理 | 证明 | 例题 | 习题 | 算法 | 易错点
    title: str = ""
    content: str = ""
    latex: str = ""
    intuitive_explanation: str = ""
    solution: str = ""
    source_document_id: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    source_span: dict[str, Any] = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    chapter_path: list[str] = field(default_factory=list)
    difficulty: int = 3
    teaching_role: str = "core"  # core | auxiliary | practice
    expected_prerequisites: list[dict[str, str]] = field(default_factory=list)
    provenance: str = "manual"  # rule | llm | teacher | manual
    confidence: float = 1.0
    review_status: str = "verified"  # draft | verified | rejected | deprecated
    reviewer_id: str | None = None


@dataclass
class KnowledgeRelation:
    source_unit_id: str
    target_unit_id: str
    relation_type: str  # prerequisite | supports_proof | derives | applies_to | example_of | exercise_of | common_mistake_of | similar_to | contrast_with | algorithm_of | code_task_of
    confidence: float = 1.0
    provenance: str = "rule"  # rule | llm | teacher
    review_status: str = "verified"  # draft | verified | rejected | deprecated


@dataclass
class EvidencePack:
    query_scope: dict[str, str] = field(default_factory=dict)
    direct_hits: list[KnowledgeHit] = field(default_factory=list)
    graph_hits: list[KnowledgeHit] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0
    teaching_hints: list[dict[str, Any]] = field(default_factory=list)



