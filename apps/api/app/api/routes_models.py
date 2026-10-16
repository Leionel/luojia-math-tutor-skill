from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.auth import Principal, get_forwarded_llm_key, get_principal
from app.config import MODEL_PROVIDERS, PROVIDER_BASE_URLS, Settings, configured_model_catalog
from app.llm.openai_compatible import OpenAICompatibleClient
from app.main_deps import get_app_settings


router = APIRouter(prefix="/api/models", tags=["models"])


class TestModelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str | None = None


class ModelItem(BaseModel):
    id: str
    name: str
    provider: str


class ProviderItem(BaseModel):
    id: str
    label: str
    base_url: str  # empty for "custom": the user supplies their own endpoint


class ModelListResponse(BaseModel):
    default_model: str
    allowed_models: list[str]
    models: list[ModelItem]
    providers: list[ProviderItem]


@router.get("", response_model=ModelListResponse)
async def list_models(
    settings: Settings = Depends(get_app_settings),
    _principal: Principal = Depends(get_principal),
):
    catalog = configured_model_catalog()
    return ModelListResponse(
        default_model=settings.llm_model,
        allowed_models=sorted(catalog),
        models=[
            ModelItem(id=model_id, name=spec.name, provider=spec.provider)
            for model_id, spec in catalog.items()
        ],
        providers=[
            ProviderItem(id=provider_id, label=label, base_url=PROVIDER_BASE_URLS.get(provider_id, ""))
            for provider_id, label in MODEL_PROVIDERS.items()
        ],
    )


@router.post("/test")
async def test_model(
    payload: TestModelRequest,
    settings: Settings = Depends(get_app_settings),
    _principal: Principal = Depends(get_principal),
    user_api_key: str | None = Depends(get_forwarded_llm_key),
):
    return await OpenAICompatibleClient(settings).test(user_api_key, payload.model)
