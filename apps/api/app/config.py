import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


PROVIDER_BASE_URLS: dict[str, str] = {
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "moonshot": "https://api.moonshot.cn/v1",
    "glm": "https://open.bigmodel.cn/api/paas/v4"
}
LOCAL_AUTH_SECRET = "local-development-only-change-before-production"

@dataclass(frozen=True)
class ModelSpec:
    name: str
    provider: str
    vision: bool = False


# Keep this deliberately small. These identifiers were checked against the
# providers' public API docs on 2026-09-08. Operators can add an exact model
# through EXTRA_MODELS without changing the source.
MODEL_CATALOG: dict[str, ModelSpec] = {
    "deepseek-v4-flash": ModelSpec("DeepSeek V4 Flash", "deepseek"),
    "deepseek-v4-pro": ModelSpec("DeepSeek V4 Pro", "deepseek"),
    "qwen-plus": ModelSpec("Qwen Plus", "qwen"),
    "qwen3.5-plus": ModelSpec("Qwen 3.5 Plus", "qwen"),
    "qwen3.6-plus": ModelSpec("Qwen 3.6 Plus", "qwen"),
    "kimi-k3": ModelSpec("Kimi K3", "moonshot", vision=True),
    "kimi-k2.6": ModelSpec("Kimi K2.6", "moonshot", vision=True),
    "glm-4.7": ModelSpec("GLM-4.7", "glm"),
    "glm-4.7-flash": ModelSpec("GLM-4.7 Flash", "glm"),
    "glm-4.6v-flash": ModelSpec("GLM-4.6V Flash", "glm", vision=True),
}


def configured_model_catalog() -> dict[str, ModelSpec]:
    catalog = dict(MODEL_CATALOG)
    for model_id in filter(None, (part.strip() for part in os.getenv("EXTRA_MODELS", "").split(","))):
        provider = model_id.split("-", 1)[0]
        if provider == "kimi":
            provider = "moonshot"
        if provider not in PROVIDER_BASE_URLS:
            raise ValueError(
                f"EXTRA_MODELS contains unsupported provider for {model_id!r}"
            )
        catalog[model_id] = ModelSpec(model_id, provider)
    return catalog


ALLOWED_MODELS = frozenset(configured_model_catalog())


class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "local")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./luojia_tutor.db")
    llm_provider: str = os.getenv("LLM_PROVIDER", "deepseek")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    vision_model: str = os.getenv("VISION_MODEL", "glm-4.6v-flash")
    allow_user_api_key: bool = os.getenv("ALLOW_USER_API_KEY", "false").lower() == "true"
    cors_origins_csv: str = os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000",
    )
    auth_required: bool = os.getenv("AUTH_REQUIRED", "false").lower() == "true"
    auth_token_secret: str = os.getenv("AUTH_TOKEN_SECRET", LOCAL_AUTH_SECRET)
    auth_token_ttl_seconds: int = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400"))
    demo_user_id: str = os.getenv("DEMO_USER_ID", "demo-user")
    initial_mastery: float = float(os.getenv("INITIAL_MASTERY", "0.5"))
    default_difficulty: int = int(os.getenv("DEFAULT_DIFFICULTY", "3"))
    remediation_error_threshold: int = int(
        os.getenv("REMEDIATION_ERROR_THRESHOLD", "2")
    )
    remediation_mastery_threshold: float = float(
        os.getenv("REMEDIATION_MASTERY_THRESHOLD", "0.3")
    )
    hint_error_light: int = int(os.getenv("HINT_ERROR_LIGHT", "1"))
    hint_error_formula: int = int(os.getenv("HINT_ERROR_FORMULA", "2"))
    hint_error_near_answer: int = int(os.getenv("HINT_ERROR_NEAR_ANSWER", "3"))
    hint_mastery_formula: float = float(os.getenv("HINT_MASTERY_FORMULA", "0.2"))
    hint_mastery_light: float = float(os.getenv("HINT_MASTERY_LIGHT", "0.4"))
    bkt_slip_probability: float = float(os.getenv("BKT_SLIP_PROBABILITY", "0.10"))
    bkt_guess_independent: float = float(os.getenv("BKT_GUESS_INDEPENDENT", "0.10"))
    bkt_guess_light_hint: float = float(os.getenv("BKT_GUESS_LIGHT_HINT", "0.40"))
    bkt_guess_heavy_hint: float = float(os.getenv("BKT_GUESS_HEAVY_HINT", "0.80"))
    bkt_learn_independent: float = float(os.getenv("BKT_LEARN_INDEPENDENT", "0.15"))
    bkt_learn_light_hint: float = float(os.getenv("BKT_LEARN_LIGHT_HINT", "0.05"))
    bkt_learn_heavy_hint: float = float(os.getenv("BKT_LEARN_HEAVY_HINT", "0.00"))
    semantic_cache_ttl_seconds: int = int(
        os.getenv("SEMANTIC_CACHE_TTL_SECONDS", "86400")
    )
    semantic_worker_poll_seconds: float = float(
        os.getenv("SEMANTIC_WORKER_POLL_SECONDS", "1.0")
    )
    tool_timeout_seconds: int = int(os.getenv("TOOL_TIMEOUT_SECONDS", "8"))
    tool_max_rounds: int = int(os.getenv("TOOL_MAX_ROUNDS", "2"))

    def resolve_model(self, request_model: str | None) -> str:
        model = request_model or self.llm_model
        if model not in configured_model_catalog():
            raise ValueError(
                f"Unsupported model {model!r}. Choose a model returned by /api/models."
            )
        return model

    def resolve_base_url(self, resolved_model: str) -> str:
        spec = configured_model_catalog().get(resolved_model)
        if not spec:
            raise ValueError(f"Unsupported model {resolved_model!r}")
        if resolved_model == self.llm_model and self.llm_base_url:
            return self.llm_base_url
        return PROVIDER_BASE_URLS[spec.provider]

    @property
    def cors_origins(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins_csv.split(",") if item.strip()]
        if "*" in origins:
            raise ValueError("CORS_ORIGINS must contain explicit origins, not '*'.")
        return origins

    def validate_runtime(self) -> None:
        self.resolve_model(None)
        self.resolve_model(self.vision_model)
        if self.auth_required and len(self.auth_token_secret) < 32:
            raise ValueError(
                "AUTH_TOKEN_SECRET must contain at least 32 characters when AUTH_REQUIRED=true."
            )
        if self.app_env.lower() in {"prod", "production"}:
            if not self.auth_required:
                raise ValueError("AUTH_REQUIRED must be true in production.")
            if self.auth_token_secret == LOCAL_AUTH_SECRET:
                raise ValueError("Set a unique AUTH_TOKEN_SECRET in production.")
        if not 0.0 <= self.initial_mastery <= 1.0:
            raise ValueError("INITIAL_MASTERY must be between 0 and 1.")
        if not 1 <= self.default_difficulty <= 5:
            raise ValueError("DEFAULT_DIFFICULTY must be between 1 and 5.")
        probabilities = {
            "REMEDIATION_MASTERY_THRESHOLD": self.remediation_mastery_threshold,
            "HINT_MASTERY_FORMULA": self.hint_mastery_formula,
            "HINT_MASTERY_LIGHT": self.hint_mastery_light,
            "BKT_SLIP_PROBABILITY": self.bkt_slip_probability,
            "BKT_GUESS_INDEPENDENT": self.bkt_guess_independent,
            "BKT_GUESS_LIGHT_HINT": self.bkt_guess_light_hint,
            "BKT_GUESS_HEAVY_HINT": self.bkt_guess_heavy_hint,
            "BKT_LEARN_INDEPENDENT": self.bkt_learn_independent,
            "BKT_LEARN_LIGHT_HINT": self.bkt_learn_light_hint,
            "BKT_LEARN_HEAVY_HINT": self.bkt_learn_heavy_hint,
        }
        for name, value in probabilities.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1.")
        if not self.hint_mastery_formula <= self.hint_mastery_light:
            raise ValueError("Hint mastery thresholds must be ordered.")
        if not self.hint_error_light <= self.hint_error_formula <= self.hint_error_near_answer:
            raise ValueError("Hint error thresholds must be ordered.")
        if self.semantic_cache_ttl_seconds < 0 or self.semantic_worker_poll_seconds <= 0:
            raise ValueError("Semantic cache and worker timing must be non-negative.")
        if not 0 <= self.tool_max_rounds <= 2 or not 1 <= self.tool_timeout_seconds <= 10:
            raise ValueError("Tool limits exceed the sandbox safety envelope.")

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

    @property
    def upload_root(self) -> Path:
        configured = os.getenv("UPLOAD_ROOT")
        if configured:
            return (self.repo_root / configured).resolve()
        return (self.repo_root / "apps" / "api" / "data" / "uploads").resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
