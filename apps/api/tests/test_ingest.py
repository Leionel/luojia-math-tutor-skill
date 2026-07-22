import tempfile
from pathlib import Path
from app.knowledge.pipeline.ingest import create_source_document, calculate_sha256, estimate_page_count


def test_create_source_document_and_checksum():
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Linear Algebra\n<!-- PAGE: 1 -->\nDefinition 1\n<!-- PAGE: 3 -->\nTheorem 1\n")
        temp_path = Path(f.name)

    try:
        doc = create_source_document(temp_path, course_id="la_101")
        assert doc.course_id == "la_101"
        assert doc.filename == temp_path.name
        assert doc.page_count == 3
        assert doc.checksum == calculate_sha256(temp_path)
        assert doc.status == "active"
    finally:
        if temp_path.exists():
            temp_path.unlink()
