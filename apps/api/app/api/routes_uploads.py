import re
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse

from app.services.mineru_client import extract_markdown_agent_api
from app.config import get_settings
from app.knowledge.document_chunking import chunk_document
from app.main_deps import get_repository, ensure_reference_help_allowed
from app.memory.repository import Repository
from app.auth import Principal, get_principal

router = APIRouter(prefix="/api/uploads", tags=["uploads"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = get_settings().upload_root
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# Aligned with the MinerU per-file limit (200MB); textbooks up to 200 pages
# are accepted for note generation.
MAX_UPLOAD_BYTES = 200 * 1024 * 1024
MAX_PDF_PAGES = 200
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "pdf", "pptx", "docx", "doc"}
SAFE_UPLOAD_NAME = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\."
    r"(?:png|jpg|jpeg|webp|gif|pdf|pptx|docx|doc)$",
    re.IGNORECASE,
)


def _upload_dir() -> Path:
    path = Path(UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_extension(filename: str) -> str:
    suffix = Path(filename or "upload.png").name.rsplit(".", 1)
    ext = suffix[-1].lower() if len(suffix) == 2 else "png"
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported upload file type")
    return ext


async def _read_limited_upload(file: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="文件超过 200MB 上传限制，请拆分后重新上传。",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _pdf_page_count(data: bytes) -> int:
    # Rough count from the raw PDF structure; good enough as an upload guard.
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def _resolve_uploaded_file(filename: str) -> Path | None:
    if not SAFE_UPLOAD_NAME.fullmatch(filename):
        return None
    base = _upload_dir().resolve()
    path = (base / filename).resolve()
    try:
        path.relative_to(base)
    except ValueError:
        return None
    return path

@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
):
    if not principal.authenticated:
        raise HTTPException(status_code=401, detail="Sign in to upload files.")
    ensure_reference_help_allowed(principal.user_id)
    filename_attr = getattr(file, "filename", "") or ""
    ext = _safe_extension(filename_attr)
    data = await _read_limited_upload(file)
    if not data:
        raise HTTPException(422, "文件为空，请重新选择。")
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{ext}"
    filepath = _upload_dir() / filename
    
    try:
        filepath.write_bytes(data)
    except OSError as exc:
        filepath.unlink(missing_ok=True)
        raise HTTPException(507, "上传未保存：本地存储不可用，请稍后重试。") from exc

    if ext.lower() == "pdf" and _pdf_page_count(data) > MAX_PDF_PAGES:
        filepath.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413,
            detail=f"PDF 超过 {MAX_PDF_PAGES} 页限制，请拆分章节后重新上传。",
        )

    is_document = ext.lower() in ("pdf", "pptx", "docx", "doc")
    document_id = None
    extracted_md = ""
    parse_error: str | None = None

    try:
        extracted_md = await extract_markdown_agent_api(str(filepath.resolve()))
    except Exception as e:
        logger.warning("MinerU extraction failed: %s", e)
        parse_error = str(e)
        if is_document:
            # Nothing was stored, so the caller must not be told this succeeded.
            # Returning the error text in `markdown` would let it be persisted
            # and later served as if it were document content.
            filepath.unlink(missing_ok=True)
            raise HTTPException(
                status_code=502,
                detail=f"文档解析失败，未入库，请重试或改用图片上传：{e}",
            ) from e

    if is_document and (not isinstance(extracted_md, str) or not extracted_md.strip()):
        filepath.unlink(missing_ok=True)
        raise HTTPException(502, "解析未得到可读原文，资料未入库，请检查文件后重试。")
    try:
        # Re-check after the long external request: an assessment may have begun.
        ensure_reference_help_allowed(principal.user_id)
        if is_document:
            document_id = repo.save_parsed_upload(
                Path(filename_attr.replace("\\", "/")).name, principal.user_id, extracted_md,
                chunk_document(extracted_md), filename)
        else:
            repo.record_uploaded_file(filename, principal.user_id)
    except HTTPException:
        filepath.unlink(missing_ok=True)
        raise
    except Exception as exc:
        filepath.unlink(missing_ok=True)
        logger.exception("Parsed upload persistence failed")
        raise HTTPException(503, "解析结果未能保存，未建立资料，请稍后重新上传。") from exc

    return {
        "url": f"/api/uploads/{filename}",
        "markdown": extracted_md,
        "document_id": document_id,
        "parse_error": parse_error,
    }

@router.get("/documents")
def list_documents(
    principal: Principal = Depends(get_principal),
    repo: Repository = Depends(get_repository),
):
    if not principal.authenticated:
        raise HTTPException(401, "请先登录查看自己的资料。")
    return {"documents": repo.list_documents(principal.user_id)}


@router.get("/{filename}")
async def get_uploaded_image(
    filename: str,
    principal: Principal = Depends(get_principal),
    repo: Repository = Depends(get_repository),
):
    if not principal.authenticated:
        raise HTTPException(status_code=401, detail="Sign in to view uploads.")
    filepath = _resolve_uploaded_file(filename)
    if not filepath or not repo.uploaded_file_belongs_to(filename, principal.user_id) or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Upload not found")
    return FileResponse(filepath, headers={"Cache-Control": "private, no-store"})
