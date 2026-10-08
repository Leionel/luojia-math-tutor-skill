import time
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field,ConfigDict

from app.auth import (
    Principal,
    get_principal,
    hash_password,
    issue_token,
    decode_claims,
    _bearer,
    verify_password,
)
from app.config import Settings
from app.main_deps import get_app_settings, get_repository
from app.memory.repository import Repository


router = APIRouter(prefix="/api/auth", tags=["auth"])


class CredentialsRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    user_id: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.@-]+$")
    password: str = Field(min_length=10, max_length=256)
    display_name: str | None = Field(default=None, max_length=80)


def _prepare_session(user_id: str, settings: Settings):
    if type(settings.auth_token_ttl_seconds) is not int or not 1<=settings.auth_token_ttl_seconds<=31*86400:
        raise HTTPException(503,"账号会话有效期配置不可用，请稍后重试。")
    sid=uuid4().hex
    expires_at=int(time.time())+settings.auth_token_ttl_seconds
    try:
        token=issue_token(user_id,settings,sid=sid,expires_at=expires_at)
    except ValueError as exc:
        raise HTTPException(503,"账号签发服务暂不可用，请稍后重试。") from exc
    return {"access_token":token,"token_type":"bearer","expires_in":settings.auth_token_ttl_seconds,"user_id":user_id,"auth_version":2},sid,expires_at


@router.post("/register", status_code=201)
def register(
    payload: CredentialsRequest,
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
):
    response,sid,expires_at=_prepare_session(payload.user_id,settings)
    password_hash,salt=hash_password(payload.password)
    created=repo.create_auth_user_with_session(payload.user_id,payload.display_name or payload.user_id,password_hash,salt,sid,expires_at)
    if not created:raise HTTPException(409,"User already exists.")
    return response


@router.post("/login")
def login(
    payload: CredentialsRequest,
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
):
    user = repo.get_auth_user(payload.user_id)
    if not user or not verify_password(
        payload.password,
        str(user.get("password_hash") or ""),
        str(user.get("password_salt") or ""),
    ):
        raise HTTPException(status_code=401, detail="Invalid user ID or password.")
    response,sid,expires_at=_prepare_session(payload.user_id,settings)
    repo.create_auth_session(sid,payload.user_id,expires_at)
    return response


@router.get("/me")
def me(principal: Principal = Depends(get_principal)):
    return {"user_id":principal.user_id,"authenticated":principal.authenticated,"access_mode":"account" if principal.authenticated else "demo","role":principal.role}

@router.post("/logout")
def logout(credentials:HTTPAuthorizationCredentials|None=Depends(_bearer),repo:Repository=Depends(get_repository),settings:Settings=Depends(get_app_settings)):
    if not credentials:raise HTTPException(401,"Authentication is required.")
    claims=decode_claims(credentials.credentials,settings,require_session=True)
    if not repo.revoke_auth_session(claims['sid'],claims['sub']):raise HTTPException(401,"Authentication session was not found.")
    return {"revoked":True,"scope":"current_session"}
