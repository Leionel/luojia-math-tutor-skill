from functools import lru_cache
from pathlib import Path
import os

from pydantic import BaseModel


PROVIDER_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "glm": "https://open.bigmodel.cn/api/paas/v4"
}

ALLOWED_MODELS = {
    # DeepSeek
    "deepseek-v4-flash", "deepseek-v4-pro", "deepseek-chat", "deepseek-reasoner",
    # Qwen
    "qwen-max", "qwen-plus", "qwen-turbo", "qwen-math-plus",
    # Moonshot
    "moonshot-v1-8k", "moonshot-v1-32k",
    # Zhipu
    "glm-4", "glm-4-flash", "glm-4v"
}


class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "local")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./luojia_tutor.db")
    llm_provider: str = os.getenv("LLM_PROVIDER", "deepseek")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "sk-5fb21dc286524aab8558e739e64dce08")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    allow_user_api_key: bool = os.getenv("ALLOW_USER_API_KEY", "true").lower() == "true"

    def resolve_model(self, request_model: str | None) -> str:
        if request_model and request_model in ALLOWED_MODELS:
            return request_model
        if self.llm_model in ALLOWED_MODELS:
            return self.llm_model
        return "deepseek-chat"

    def resolve_base_url(self, resolved_model: str) -> str:
        if "qwen" in resolved_model:
            return PROVIDER_BASE_URLS["qwen"]
        if "moonshot" in resolved_model:
            return PROVIDER_BASE_URLS["moonshot"]
        if "glm" in resolved_model:
            return PROVIDER_BASE_URLS["glm"]
        return PROVIDER_BASE_URLS["deepseek"]

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def knowledge_root(self) -> Path:
        configured = os.getenv("KNOWLEDGE_ROOT")
        if configured:
            return (self.repo_root / configured).resolve()
        return self.repo_root / "luojia-math-tutor" / "references"

    @property
    def skill_file(self) -> Path:
        configured = os.getenv("SKILL_FILE")
        if configured:
            return (self.repo_root / configured).resolve()
        return self.repo_root / "luojia-math-tutor" / "SKILL.md"


@lru_cache
def get_settings() -> Settings:
    return Settings()

