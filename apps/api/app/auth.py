import base64
import hashlib
import hmac
import json
import os
import re
import time
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings
from app.main_deps import get_app_settings


_USER_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{2,63}$")
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: str
    authenticated: bool


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    return _b64_encode(digest), _b64_encode(salt)


def verify_password(password: str, expected_hash: str, salt: str) -> bool:
    try:
        actual, _ = hash_password(password, _b64_decode(salt))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected_hash)


def issue_token(user_id: str, settings: Settings) -> str:
    if len(settings.auth_token_secret) < 32:
        raise ValueError("AUTH_TOKEN_SECRET is not configured.")
    payload = {
        "sub": user_id,
        "exp": int(time.time()) + settings.auth_token_ttl_seconds,
        "v": 1,
    }
    encoded = _b64_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        settings.auth_token_secret.encode("utf-8"),
        encoded.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded}.{_b64_encode(signature)}"


def decode_token(token: str, settings: Settings) -> str:
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(
            settings.auth_token_secret.encode("utf-8"),
            encoded.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(_b64_decode(signature), expected):
            raise ValueError("signature")
        payload = json.loads(_b64_decode(encoded))
        user_id = str(payload["sub"])
        if int(payload["exp"]) < int(time.time()) or not _USER_ID.fullmatch(user_id):
            raise ValueError("expired")
        return user_id
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_app_settings),
) -> Principal:
    if credentials:
        return Principal(decode_token(credentials.credentials, settings), True)
    if settings.auth_required:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
        )
    return Principal(settings.demo_user_id, False)


def resolve_user_id(
    principal: Principal,
    requested_user_id: str | None,
    settings: Settings,
) -> str:
    if principal.authenticated or settings.auth_required:
        if requested_user_id and requested_user_id != principal.user_id:
            raise HTTPException(status_code=403, detail="Cross-user access is forbidden.")
        return principal.user_id
    # Explicitly local/demo compatibility. Production never trusts this field.
    return requested_user_id or principal.user_id


def get_forwarded_llm_key(
    x_luojia_llm_key: str | None = Header(default=None),
    settings: Settings = Depends(get_app_settings),
) -> str | None:
    if not x_luojia_llm_key:
        return None
    if not settings.allow_user_api_key:
        raise HTTPException(status_code=403, detail="User API key forwarding is disabled.")
    if len(x_luojia_llm_key) > 512 or "\n" in x_luojia_llm_key:
        raise HTTPException(status_code=400, detail="Invalid forwarded model key.")
    # The key exists only in this request dependency and is never logged/stored.
    return x_luojia_llm_key


def ensure_session_access(
    session_id: str,
    principal: Principal,
    settings: Settings,
    repository,
) -> None:
    if not (principal.authenticated or settings.auth_required):
        return
    if not repository.session_belongs_to(session_id, principal.user_id):
        raise HTTPException(status_code=404, detail="Session was not found.")


def request_principal(request: Request) -> Principal | None:
    return getattr(request.state, "principal", None)
