from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class Session:
    id: str
    user_id: str
    title: str
    subject: str
    created_at: str
    updated_at: str


@dataclass
class Message:
    id: str
    session_id: str
    role: str
    content: str
    intent: Optional[str]
    created_at: str

