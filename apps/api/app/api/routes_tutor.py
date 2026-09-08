from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from starlette.responses import StreamingResponse

from app.auth import (
    Principal,
    ensure_session_access,
    get_forwarded_llm_key,
    get_principal,
    resolve_user_id,
)
from app.config import Settings
from app.main_deps import get_app_settings, get_orchestrator
from app.tutor.orchestrator import TutorOrchestrator


router = APIRouter(prefix="/api/tutor", tags=["tutor"])


class TutorStreamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    user_id: str = "demo-user"
    message: str
    subject: str = "auto"
    mode: str = "socratic"
    model: str | None = None
    requested_hint: bool = False
    image_urls: list[str] | None = None


@router.post("/stream")
async def stream_tutor(
    payload: TutorStreamRequest,
    orchestrator: TutorOrchestrator = Depends(get_orchestrator),
    principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
    user_api_key: str | None = Depends(get_forwarded_llm_key),
):
    user_id = resolve_user_id(principal, payload.user_id, settings)
    ensure_session_access(payload.session_id, principal, settings, orchestrator.repository)
    try:
        settings.resolve_model(payload.model)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return StreamingResponse(
        orchestrator.stream_reply(
            session_id=payload.session_id,
            user_id=user_id,
            message=payload.message,
            subject=payload.subject,
            mode=payload.mode,
            user_api_key=user_api_key,
            model=payload.model,
            requested_hint=payload.requested_hint,
            image_urls=payload.image_urls,
        ),
        media_type="text/event-stream",
    )

class TitleGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str
    model: str | None = None

@router.post("/generate_title")
async def generate_title(
    payload: TitleGenerateRequest,
    orchestrator: TutorOrchestrator = Depends(get_orchestrator),
    _principal: Principal = Depends(get_principal),
    settings: Settings = Depends(get_app_settings),
    user_api_key: str | None = Depends(get_forwarded_llm_key),
):
    try:
        settings.resolve_model(payload.model)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    prompt = [
        {"role": "system", "content": "你是一个标题和标签生成器。根据用户的第一条输入，提炼出不多于10个字的简短核心标题，以及一个2-5字的分类大标签(如微积分/概率论/线性代数/物理/编程/综合等)。必须严格以 '标题|标签' 的格式输出，不能包含任何多余解释或标点符号。"},
        {"role": "user", "content": payload.message}
    ]
    response = await orchestrator.llm.chat_completion(
        messages=prompt,
        api_key=user_api_key,
        model=payload.model
    )
    title = payload.message[:10] + "..." if len(payload.message) > 10 else payload.message
    label = "综合"
    if response and "|" in response:
        parts = response.split("|", 1)
        title = parts[0].strip()
        label = parts[1].strip()
        
    return {"title": title, "label": label}
