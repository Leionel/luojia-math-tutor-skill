import os
import uuid
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse

from app.services.mineru_client import extract_markdown_agent_api
from app.main_deps import get_repository
from app.memory.repository import Repository

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    ext = filename_attr.split('.')[-1] if '.' in filename_attr else 'png'
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as f:
        f.write(await file.read())
        
    document_id = None
    try:
        abs_filepath = os.path.abspath(filepath)
        extracted_md = await extract_markdown_agent_api(abs_filepath)
        
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
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    return {"error": "Not found"}
