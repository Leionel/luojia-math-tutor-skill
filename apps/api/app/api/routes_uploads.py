import re
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse

from app.services.mineru_client import extract_markdown_agent_api
from app.main_deps import get_repository
from app.memory.repository import Repository

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
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
            raise HTTPException(status_code=413, detail="Upload exceeds 10MB limit")
        chunks.append(chunk)
    return b"".join(chunks)


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

def chunk_markdown(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

@router.post("")
async def upload_image(
    file: UploadFile = File(...),
    repo: Repository = Depends(get_repository)
):
    filename_attr = getattr(file, "filename", "") or ""
    ext = _safe_extension(filename_attr)
    data = await _read_limited_upload(file)
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{ext}"
    filepath = _upload_dir() / filename
    
    filepath.write_bytes(data)
        
    document_id = None
    try:
        extracted_md = await extract_markdown_agent_api(str(filepath.resolve()))
        
        # If the file is a document (pdf, pptx, docx), store it for Implicit RAG
        if ext.lower() in ['pdf', 'pptx', 'docx', 'doc']:
            document_id = repo.insert_document(filename_attr, "demo-user")
            chunks = chunk_markdown(extracted_md)
            repo.insert_document_chunks(document_id, chunks)
            
    except Exception as e:
        print(f"MinerU Error: {e}")
        extracted_md = f"⚠️ [MinerU 网络解析失败: {e}]"
        
    return {
        "url": f"/api/uploads/{filename}",
        "markdown": extracted_md,
        "document_id": document_id
    }

@router.get("/{filename}")
async def get_uploaded_image(filename: str):
    filepath = _resolve_uploaded_file(filename)
    if filepath and filepath.exists():
        return FileResponse(filepath)
    raise HTTPException(status_code=404, detail="Upload not found")
