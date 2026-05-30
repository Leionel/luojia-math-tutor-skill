from dataclasses import dataclass


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


@dataclass
class KnowledgeHit:
    item: KnowledgeItem
    score: int

