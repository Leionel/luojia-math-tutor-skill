import json
from typing import AsyncIterator

import httpx

from app.config import Settings


class OpenAICompatibleClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def stream(
        self, messages: list[dict[str, str]], api_key: str | None = None, model: str | None = None
    ) -> AsyncIterator[str]:
        key = api_key if self.settings.allow_user_api_key and api_key else self.settings.llm_api_key
        resolved_model = self.settings.resolve_model(model)
        if not key:
            async for token in self._fallback_stream(messages):
                yield token
            return

        base_url = self.settings.resolve_base_url(resolved_model)
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.3,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
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
                        if content:
                            yield content
                    except Exception:
                        continue

    async def chat_completion(
        self, messages: list[dict[str, str]], api_key: str | None = None, model: str | None = None
    ) -> str:
        key = api_key if self.settings.allow_user_api_key and api_key else self.settings.llm_api_key
        resolved_model = self.settings.resolve_model(model)
        if not key:
            return ""
        base_url = self.settings.resolve_base_url(resolved_model)
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
            "temperature": 0.1,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return ""

    async def test(self, api_key: str | None = None, model: str | None = None) -> dict[str, str | bool]:
        key = api_key if self.settings.allow_user_api_key and api_key else self.settings.llm_api_key
        resolved_model = self.settings.resolve_model(model)
        if not key:
            return {"ok": False, "message": "未配置 API Key；本地 fallback 可用，但不会调用远程模型。"}
        base_url = self.settings.resolve_base_url(resolved_model)
        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": resolved_model,
            "messages": [{"role": "user", "content": "ping"}],
            "stream": False,
            "max_tokens": 4,
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
            return {"ok": True, "message": "模型连接成功。"}
        except Exception as exc:
            return {"ok": False, "message": f"模型连接失败：{exc}"}

    async def _fallback_stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        user = messages[-1]["content"]
        system = messages[0]["content"]
        if "POWER_INTEGRAL_MISSING_DIVISOR" in system or "x^3" in user:
            text = (
                "### 考点分析\n这题考的是幂函数积分。\n\n"
                "### 当前判断\n你的方向是对的：$x^2$ 的原函数确实会和 $x^3$ 有关。"
                "不过少了一个系数。后台检查：对 $x^3$ 求导会得到 $3x^2$，不是 $x^2$。\n\n"
                "### 提示\n你还记得 $\\int x^n dx$ 的公式里，分母应该是什么吗？"
            )
        elif "互斥" in user and "独立" in user:
            text = (
                "### 考点分析\n这题考的是事件关系：互斥和独立。\n\n"
                "### 当前判断\n互斥表示两个事件不能同时发生；独立表示一个事件发生不影响另一个事件概率。"
                "这两个概念一般不能直接等同。\n\n"
                "### 提示\n你可以想想：如果 $A$ 和 $B$ 互斥且 $P(A),P(B)>0$，那么 $P(AB)$ 是多少？"
            )
        else:
            text = (
                "### 考点分析\n我会先定位题型，再给你下一步提示。\n\n"
                "### 当前判断\n本地 fallback 已接管回复；配置 DeepSeek 或用户 API Key 后可使用远程模型生成更完整的讲解。\n\n"
                "### 提示\n先把你的题目或当前推导写成一个明确的等式，我来帮你检查下一步。"
            )
        for index in range(0, len(text), 12):
            yield text[index : index + 12]
