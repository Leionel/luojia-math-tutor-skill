import json
import logging
import os
from typing import Any, AsyncIterator

import httpx

from app.config import Settings, PROVIDER_BASE_URLS

logger = logging.getLogger(__name__)


class OpenAICompatibleClient:
    _http_client: httpx.AsyncClient | None = None

    @classmethod
    def get_http_client(cls) -> httpx.AsyncClient:
        if cls._http_client is None or cls._http_client.is_closed:
            cls._http_client = httpx.AsyncClient(timeout=60.0)
        return cls._http_client

    def __init__(self, settings: Settings):
        self.settings = settings

    async def stream(
        self,
        messages: list[dict[str, Any]],
        api_key: str | None = None,
        model: str | None = None,
    ) -> AsyncIterator[str | dict[str, str]]:
        key = api_key if self.settings.allow_user_api_key and api_key else self.settings.llm_api_key
        base_url, resolved_model = self.settings.resolve_request(model)
        if not key:
            yield {
                "type": "content",
                "content": (
                    "⚠️ 当前服务未配置模型 API Key，因此没有生成数学解答。"
                    "请由管理员设置 LLM_API_KEY 后重试。"
                ),
            }
            return

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.3,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        client = self.get_http_client()
        async with client.stream("POST", url, json=payload, headers=headers, timeout=60.0) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line.removeprefix("data: ").strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content")
                    reasoning_content = delta.get("reasoning_content")
                    if reasoning_content:
                        yield {"type": "reasoning", "content": reasoning_content}
                    if content:
                        yield {"type": "content", "content": content}
                except Exception:
                    continue

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        api_key: str | None = None,
        model: str | None = None,
    ) -> str:
        key = api_key if self.settings.allow_user_api_key and api_key else self.settings.llm_api_key
        base_url, resolved_model = self.settings.resolve_request(model)
        if not key:
            raise RuntimeError(
                "未配置模型 API Key。请在服务端设置 LLM_API_KEY。"
            )
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
            "temperature": 0.1,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            client = self.get_http_client()
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error("chat_completion failed: %s", e)
            raise

    async def test(self, api_key: str | None = None, model: str | None = None) -> dict[str, str | bool]:
        key = api_key if self.settings.allow_user_api_key and api_key else self.settings.llm_api_key
        try:
            base_url, resolved_model = self.settings.resolve_request(model)
        except ValueError as exc:
            return {"ok": False, "message": str(exc)}
        if not key:
            return {"ok": False, "message": "未配置 API Key；离线假回复已禁用。"}
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": resolved_model,
            "messages": [{"role": "user", "content": "ping"}],
            "stream": False,
            "max_tokens": 4,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            client = self.get_http_client()
            response = await client.post(url, json=payload, headers=headers, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            returned_model = str(data.get("model") or resolved_model)
            return {
                "ok": True,
                "message": "模型连接成功。",
                "model": returned_model,
                "provider": base_url,
            }
        except Exception as exc:
            return {"ok": False, "message": f"模型连接失败：{exc}"}

    async def create_embedding(
        self, text: str, api_key: str | None = None, model: str | None = None
    ) -> list[float]:
        # 1. 确定 resolved_model
        resolved_model = model
        if not resolved_model:
            if self.settings.llm_provider == "qwen":
                resolved_model = "text-embedding-v3"
            elif self.settings.llm_provider == "glm":
                resolved_model = "embedding-3"
            elif self.settings.llm_provider == "moonshot":
                resolved_model = "moonshot-embed"
            else:
                resolved_model = "text-embedding-v3"

        # 2. 确定 target_provider
        target_provider = None
        if "qwen" in resolved_model:
            target_provider = "qwen"
        elif "glm" in resolved_model:
            target_provider = "glm"
        elif "moonshot" in resolved_model:
            target_provider = "moonshot"
        elif resolved_model in ("text-embedding-v3", "text-embedding-v2", "text-embedding-v1", "text-embedding"):
            target_provider = "qwen"
        elif self.settings.llm_provider == "qwen":
            target_provider = "qwen"
        elif self.settings.llm_provider == "glm":
            target_provider = "glm"
        elif self.settings.llm_provider == "moonshot":
            target_provider = "moonshot"
        else:
            target_provider = self.settings.llm_provider

        # 3. 确定 base_url
        if target_provider == "qwen":
            base_url = PROVIDER_BASE_URLS["qwen"]
        elif target_provider == "glm":
            base_url = PROVIDER_BASE_URLS["glm"]
        elif target_provider == "moonshot":
            base_url = PROVIDER_BASE_URLS["moonshot"]
        else:
            base_url = self.settings.resolve_base_url(resolved_model)

        # 4. 解析 api_key
        # Route dependencies decide whether a request-supplied key may reach
        # this client. Internal callers and tests can also pass an already
        # authorized ephemeral key directly.
        key = api_key
        if not key:
            if target_provider == "qwen":
                key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
            elif target_provider == "glm":
                key = os.getenv("ZHIPU_API_KEY") or os.getenv("GLM_API_KEY")
            elif target_provider == "moonshot":
                key = os.getenv("MOONSHOT_API_KEY")
            
            key = key or self.settings.llm_api_key

        if not key:
            return []

        url = f"{base_url.rstrip('/')}/embeddings"
        payload = {
            "model": resolved_model,
            "input": text,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            client = self.get_http_client()
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except Exception as exc:
            logger.error(
                "Embedding API call failed for model %s (url: %s): %s",
                resolved_model,
                url,
                exc,
                exc_info=True,
            )
            return []
