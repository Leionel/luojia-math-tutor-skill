from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import Principal, ensure_session_access, get_principal, resolve_user_id
from app.config import Settings
from app.main_deps import get_app_settings, get_repository
from app.memory.repository import Repository


router = APIRouter(prefix="/api", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    user_id: str = "demo-user"
    subject: str = "综合"
    title: str | None = None
    document_id: str | None = None


@router.post("/sessions")
def create_session(
    payload: CreateSessionRequest,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, payload.user_id, settings)
    return repo.create_session(user_id, payload.subject, payload.title, payload.document_id)


@router.get("/sessions")
def list_sessions(
    user_id: str = "demo-user",
    q: str | None = None,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    user_id = resolve_user_id(principal, user_id, settings)
    return {"items": repo.list_sessions(user_id, q)}


@router.get("/sessions/{session_id}/messages")
def list_messages(
    session_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    ensure_session_access(session_id, principal, settings, repo)
    repo.recover_stale_agent_runs()
    messages = repo.list_messages(session_id)
    runs = repo.list_agent_runs(session_id,principal.user_id) if repo.session_belongs_to(session_id,principal.user_id) else []
    by_message = {run["message_id"]:run for run in runs if run["message_id"]}
    for item in messages:
        if isinstance(item.get("learning_meta"),dict):
            item["learning_meta"].pop("agent_run",None)
        if item["id"] in by_message:
            item["learning_meta"] = {**(item.get("learning_meta") or {}),"agent_run":by_message[item["id"]]}
    # Interrupted/cancelled attempts have no answer to persist. Expose a safe
    # receipt placeholder on refresh; never reconstruct a partial candidate.
    for run in runs:
        if not run["message_id"] and run["status"] in ("cancelled","interrupted","failed"):
            messages.append({"id":run["run_id"],"session_id":session_id,"role":"assistant",
                             "content":"本轮未完成，可重新发起提问。", "intent":"generation_failed",
                             "created_at":run["updated_at"],"thinking_summary":None,"thinking_elapsed_ms":None,
                             "learning_meta":{"intent":"generation_failed","verified":False,"is_correct":None,
                                              "agent_run":run,"error":{"code":"execution_incomplete","message":"本轮未完成"}}})
    messages.sort(key=lambda item:item["created_at"])
    return {"items": messages}


def _run_owner(session_id, principal, repo):
    # Even in the public demo, receipts belong to the principal's user. Do not
    # extend the legacy demo bypass to the new execution table.
    if not repo.session_belongs_to(session_id,principal.user_id):
        raise HTTPException(status_code=404,detail="Session was not found.")
    return principal.user_id


@router.get("/sessions/{session_id}/runs")
def list_runs(session_id: str, repo: Repository = Depends(get_repository),
              principal: Principal = Depends(get_principal)):
    owner = _run_owner(session_id,principal,repo)
    repo.recover_stale_agent_runs()
    return {"items":repo.list_agent_runs(session_id,owner)}


@router.get("/sessions/{session_id}/runs/{run_id}")
def get_run(session_id: str, run_id: str, repo: Repository = Depends(get_repository),
             principal: Principal = Depends(get_principal)):
    owner = _run_owner(session_id,principal,repo)
    repo.recover_stale_agent_runs()
    run = repo.get_agent_run(run_id,session_id,owner)
    if run is None:
        raise HTTPException(status_code=404,detail="Execution was not found.")
    return run


@router.get("/sessions/{session_id}/mistakes")
def list_mistakes(
    session_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    ensure_session_access(session_id, principal, settings, repo)
    return {"items": repo.list_mistakes(session_id)}


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    ensure_session_access(session_id, principal, settings, repo)
    repo.delete_session(session_id)
    return {"status": "ok"}


class RenameSessionRequest(BaseModel):
    title: str
    subject: str | None = None

@router.put("/sessions/{session_id}")
def rename_session(
    session_id: str,
    payload: RenameSessionRequest,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    ensure_session_access(session_id, principal, settings, repo)
    repo.update_session_meta(session_id, payload.title, payload.subject)
    return {"status": "ok"}




@router.delete("/sessions/{session_id}/messages/after/{message_id}")
def truncate_messages(
    session_id: str,
    message_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
):
    ensure_session_access(session_id, principal, settings, repo)
    repo.truncate_messages_after(session_id, message_id)
    return {"status": "ok"}
