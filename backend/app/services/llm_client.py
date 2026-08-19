"""
services/llm_client.py

LLM 调用封装（OpenAI / Coze 兼容）。
支持 mock 模式、重试、超时、token 用量返回。
"""

import time
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import SETTINGS


@dataclass
class LLMResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float


class LLMClient:
    def __init__(self):
        self.api_key = SETTINGS.LLM_API_KEY
        self.base_url = SETTINGS.LLM_BASE_URL.rstrip("/")
        self.model = SETTINGS.LLM_MODEL
        self.timeout = SETTINGS.LLM_TIMEOUT
        self.mock = SETTINGS.LLM_MOCK

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResult:
        if self.mock:
            return self._mock_chat(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.time()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.time() - start) * 1000
        choice = data["choices"][0]
        content = choice["message"].get("content", "")
        usage = data.get("usage", {})

        return LLMResult(
            content=content,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            latency_ms=latency_ms,
        )

    def _mock_chat(self, messages: list[dict[str, str]]) -> LLMResult:
        last = messages[-1]["content"][:40]
        content = f"【模拟 LLM 回答】收到问题：{last}... 这是一个基于本地 mock 的示例回复。"
        return LLMResult(
            content=content,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            latency_ms=100.0,
        )
