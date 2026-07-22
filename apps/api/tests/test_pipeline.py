import pytest
from app.knowledge.pipeline.extractor import extract_units_from_markdown
from app.knowledge.pipeline.relations import generate_candidate_relations
from app.knowledge.schema import SourceDocument
from app.knowledge.pipeline.validator import validate_pipeline_output


def test_pipeline_extractor_and_validation():
    sample_markdown = """# 第一章 矩阵与特征值
<!-- PAGE: 1 -->
## 第一节 特征值定义

### 定义 5.1
设 A 是 n 阶矩阵，若存在数 lambda 和非零向量 x，使得 Ax = lambda x，则称 lambda 为特征值。

<!-- PAGE: 2 -->
### 定理 5.2
根据定义 5.1，矩阵 A 的特征值等于其特征多项式的根。
"""

    doc = SourceDocument(id="doc_eigen", course_id="la_101", filename="eigen.pdf")
    units = extract_units_from_markdown(sample_markdown, source_document_id=doc.id)

    assert len(units) == 2
    u1, u2 = units[0], units[1]
    assert u1.type == "定义"
    assert u1.page_start == 1
    assert u2.type == "定理"
    assert u2.page_start == 2

    # Generate candidate relations
    relations = generate_candidate_relations(units)
    assert len(relations) == 1
    assert relations[0].source_unit_id == u1.id
    assert relations[0].target_unit_id == u2.id
    assert relations[0].relation_type == "prerequisite"

    # Validate output
    is_valid, errors = validate_pipeline_output(doc, units, relations)
    assert is_valid
    assert len(errors) == 0
