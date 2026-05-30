import os
import uuid
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import FileResponse

from app.services.mineru_client import extract_markdown_agent_api

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def upload_image(file: UploadFile = File(...)):
    filename_attr = getattr(file, "filename", "") or ""
    ext = filename_attr.split('.')[-1] if '.' in filename_attr else 'png'
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as f:
        f.write(await file.read())
        
    try:
        abs_filepath = os.path.abspath(filepath)
        extracted_md = await extract_markdown_agent_api(abs_filepath)
    except Exception as e:
        print(f"MinerU Error: {e}")
        extracted_md = f"⚠️ [MinerU 网络解析失败: {e}]"
        
    return {
        "url": f"/api/uploads/{filename}",
        "markdown": extracted_md
    }

@router.get("/{filename}")
async def get_uploaded_image(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
    return {"error": "Not found"}
