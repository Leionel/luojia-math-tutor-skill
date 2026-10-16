from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import Principal, ensure_session_access, get_principal
from app.knowledge.course_service import get_course_service
from app.main_deps import get_app_settings, get_repository
from app.tutor.root_diagnostics import RootEpisodeService

router = APIRouter(prefix="/api/root-diagnostics", tags=["root-diagnostics"])


class EpisodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(max_length=80)
    episode_id: str = Field(max_length=80)


class FeedbackAck(EpisodeRequest):
    attempt_id: str = Field(max_length=80)
    feedback_id: str = Field(max_length=80)


def service_for(session_id: str, principal: Principal):
    ensure_session_access(session_id, principal, get_app_settings(), get_repository())
    return RootEpisodeService(get_course_service("numerical_analysis"))


@router.post("/ack")
def acknowledge_feedback(payload: FeedbackAck, principal: Principal = Depends(get_principal)):
    service = service_for(payload.session_id, principal)
    try:
        return service.acknowledge(principal.user_id, payload.session_id, payload.episode_id, payload.attempt_id, payload.feedback_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="反馈不存在或不属于当前会话。")


@router.post("/probe")
def start_probe(payload: EpisodeRequest, principal: Principal = Depends(get_principal)):
    service = service_for(payload.session_id, principal)
    try:
        return service.start_probe(principal.user_id, payload.session_id, payload.episode_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Episode 不存在。")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/episodes/{episode_id}")
def replay_episode(episode_id: str, session_id: str, principal: Principal = Depends(get_principal)):
    service = service_for(session_id, principal)
    try:
        return service.replay(principal.user_id, session_id, episode_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Episode 不存在。")
