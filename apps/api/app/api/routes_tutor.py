from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.main_deps import get_orchestrator
from app.tutor.orchestrator import TutorOrchestrator


router = APIRouter(prefix="/api/tutor", tags=["tutor"])


class TutorStreamRequest(BaseModel):
    session_id: str
    user_id: str = "demo-user"
    message: str
    subject: str = "auto"
    mode: str = "socratic"
    user_api_key: str | None = None
    model: str | None = None
    requested_hint: bool = False


@router.post("/stream")
async def stream_tutor(payload: TutorStreamRequest, orchestrator: TutorOrchestrator = Depends(get_orchestrator)):
    return StreamingResponse(
        orchestrator.stream_reply(
            session_id=payload.session_id,
            user_id=payload.user_id,
            message=payload.message,
            subject=payload.subject,
            mode=payload.mode,
            user_api_key=payload.user_api_key,
            model=payload.model,
            requested_hint=payload.requested_hint,
        ),
        media_type="text/event-stream",
    )
