from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.main_deps import get_repository
from app.memory.repository import Repository


router = APIRouter(prefix="/api", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    user_id: str = "demo-user"
    subject: str = "综合"
    title: str | None = None
    document_id: str | None = None


@router.post("/sessions")
def create_session(payload: CreateSessionRequest, repo: Repository = Depends(get_repository)):
    return repo.create_session(payload.user_id, payload.subject, payload.title, payload.document_id)


@router.get("/sessions")
def list_sessions(user_id: str = "demo-user", q: str | None = None, repo: Repository = Depends(get_repository)):
    return {"items": repo.list_sessions(user_id, q)}


@router.get("/sessions/{session_id}/messages")
def list_messages(session_id: str, repo: Repository = Depends(get_repository)):
    return {"items": repo.list_messages(session_id)}


@router.get("/sessions/{session_id}/mistakes")
def list_mistakes(session_id: str, repo: Repository = Depends(get_repository)):
    return {"items": repo.list_mistakes(session_id)}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, repo: Repository = Depends(get_repository)):
    repo.delete_session(session_id)
    return {"status": "ok"}


class RenameSessionRequest(BaseModel):
    title: str
    subject: str | None = None

@router.put("/sessions/{session_id}")
def rename_session(session_id: str, payload: RenameSessionRequest, repo: Repository = Depends(get_repository)):
    repo.update_session_meta(session_id, payload.title, payload.subject)
    return {"status": "ok"}




@router.delete("/sessions/{session_id}/messages/after/{message_id}")
def truncate_messages(session_id: str, message_id: str, repo: Repository = Depends(get_repository)):
    repo.truncate_messages_after(session_id, message_id)
    return {"status": "ok"}

