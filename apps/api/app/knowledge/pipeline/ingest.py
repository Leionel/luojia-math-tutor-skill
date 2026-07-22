import hashlib
import re
from pathlib import Path
from app.knowledge.schema import SourceDocument


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def estimate_page_count(file_path: Path) -> int:
    """Estimate page count of a text/markdown or document file."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        page_matches = re.findall(r"<!--\s*PAGE:\s*(\d+)\s*-->", content, re.IGNORECASE)
        if page_matches:
            return max(int(p) for p in page_matches)
        
        # Fallback based on line count (approx 50 lines per page)
        line_count = len(content.splitlines())
        return max(1, (line_count + 49) // 50)
    except Exception:
        return 1


def create_source_document(
    file_path: Path | str,
    course_id: str = "default_course",
    owner_id: str = "system",
    parser: str = "miner_u",
) -> SourceDocument:
    """Register and create a SourceDocument from a local file."""
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    filename = path.name
    doc_id = f"doc_{path.stem}_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
    checksum = calculate_sha256(path)
    page_count = estimate_page_count(path)

    return SourceDocument(
        id=doc_id,
        course_id=course_id,
        filename=filename,
        checksum=checksum,
        parser=parser,
        parser_version="1.0",
        page_count=page_count,
        language="zh",
        owner_id=owner_id,
        access_scope="course",
        status="active",
    )
