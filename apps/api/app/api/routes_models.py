from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings
from app.llm.openai_compatible import OpenAICompatibleClient
from app.main_deps import get_app_settings


router = APIRouter(prefix="/api/models", tags=["models"])


class TestModelRequest(BaseModel):
    user_api_key: str | None = None
    model: str | None = None


@router.post("/test")
async def test_model(payload: TestModelRequest, settings: Settings = Depends(get_app_settings)):
    return await OpenAICompatibleClient(settings).test(payload.user_api_key, payload.model)
