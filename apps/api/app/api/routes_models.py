from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import ALLOWED_MODELS, Settings
from app.llm.openai_compatible import OpenAICompatibleClient
from app.main_deps import get_app_settings


router = APIRouter(prefix="/api/models", tags=["models"])


class TestModelRequest(BaseModel):
    user_api_key: str | None = None
    model: str | None = None


class ModelItem(BaseModel):
    id: str
    name: str
    provider: str


class ModelListResponse(BaseModel):
    default_model: str
    allowed_models: list[str]
    models: list[ModelItem]


MODEL_CATALOG: list[ModelItem] = [
    # DeepSeek
    ModelItem(id="deepseek-chat", name="DeepSeek Chat", provider="DeepSeek"),
    ModelItem(id="deepseek-reasoner", name="DeepSeek Reasoner", provider="DeepSeek"),
    ModelItem(id="deepseek-v4-flash", name="DeepSeek v4 Flash", provider="DeepSeek"),
    ModelItem(id="deepseek-v4-pro", name="DeepSeek v4 Pro", provider="DeepSeek"),
    # Qwen
    ModelItem(id="qwen-max", name="Qwen Max", provider="通义千问 (Qwen)"),
    ModelItem(id="qwen-plus", name="Qwen Plus", provider="通义千问 (Qwen)"),
    ModelItem(id="qwen-turbo", name="Qwen Turbo", provider="通义千问 (Qwen)"),
    ModelItem(id="qwen-math-plus", name="Qwen Math Plus", provider="通义千问 (Qwen)"),
    # Moonshot
    ModelItem(id="moonshot-v1-8k", name="Moonshot v1 8K", provider="Kimi (Moonshot)"),
    ModelItem(id="moonshot-v1-32k", name="Moonshot v1 32K", provider="Kimi (Moonshot)"),
    # Zhipu
    ModelItem(id="glm-4", name="GLM-4", provider="智谱 (ZhipuAI)"),
    ModelItem(id="glm-4-flash", name="GLM-4 Flash", provider="智谱 (ZhipuAI)"),
    ModelItem(id="glm-4v", name="GLM-4V", provider="智谱 (ZhipuAI)"),
]


@router.get("", response_model=ModelListResponse)
async def list_models(settings: Settings = Depends(get_app_settings)):
    return ModelListResponse(
        default_model=settings.llm_model,
        allowed_models=sorted(list(ALLOWED_MODELS)),
        models=MODEL_CATALOG,
    )


@router.post("/test")
async def test_model(payload: TestModelRequest, settings: Settings = Depends(get_app_settings)):
    return await OpenAICompatibleClient(settings).test(payload.user_api_key, payload.model)

