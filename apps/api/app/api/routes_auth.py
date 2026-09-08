from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import (
    Principal,
    get_principal,
    hash_password,
    issue_token,
    verify_password,
)
from app.config import Settings
from app.main_deps import get_app_settings, get_repository
from app.memory.repository import Repository


router = APIRouter(prefix="/api/auth", tags=["auth"])


class CredentialsRequest(BaseModel):
    user_id: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.@-]+$")
    password: str = Field(min_length=10, max_length=256)
    display_name: str | None = Field(default=None, max_length=80)


def _token_response(user_id: str, settings: Settings) -> dict[str, str | int]:
    try:
        token = issue_token(user_id, settings)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.auth_token_ttl_seconds,
        "user_id": user_id,
    }


@router.post("/register", status_code=201)
def register(
    payload: CredentialsRequest,
    repo: Repository = Depends(get_repository),
    settings: Settings = Depends(get_app_settings),
):
    password_hash, salt = hash_password(payload.password)
    created = repo.create_auth_user(
        payload.user_id,
        payload.display_name or payload.user_id,
        password_hash,
        salt,
    )
    if not created:
        raise HTTPException(status_code=409, detail="User already exists.")
    return _token_response(payload.user_id, settings)


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
    return _token_response(payload.user_id, settings)


@router.get("/me")
def me(principal: Principal = Depends(get_principal)):
    return {"user_id": principal.user_id, "authenticated": principal.authenticated}
