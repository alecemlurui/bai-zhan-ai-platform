"""
services/llm_client.py

LLM 调用封装（OpenAI / DeepSeek / Coze 兼容）。
支持 mock 模式、指数退避重试、超时、token 用量与费用估算、结构化异常。
"""

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import SETTINGS


class LLMError(Exception):
    """LLM 调用基础异常。"""

    def __init__(
        self, message: str, status_code: int | None = None, details: Any = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class LLMRateLimitError(LLMError):
    """触发速率限制（HTTP 429）。"""


class LLMTimeoutError(LLMError):
    """请求超时。"""


class LLMContentFilterError(LLMError):
    """内容被过滤或安全拦截。"""


class LLMUnknownError(LLMError):
    """其他未知错误。"""


@dataclass
class LLMResult:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    model: str
    raw_response: dict[str, Any] | None = None


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        retry_backoff: float | None = None,
        mock: bool | None = None,
    ):
        self.api_key = api_key if api_key is not None else SETTINGS.LLM_API_KEY
        self.base_url = (
            base_url if base_url is not None else SETTINGS.LLM_BASE_URL
        ).rstrip("/")
        self.model = model if model is not None else SETTINGS.LLM_MODEL
        self.timeout = timeout if timeout is not None else SETTINGS.LLM_TIMEOUT
        self.max_retries = (
            max_retries if max_retries is not None else SETTINGS.LLM_MAX_RETRIES
        )
        self.retry_backoff = (
            retry_backoff if retry_backoff is not None else SETTINGS.LLM_RETRY_BACKOFF
        )
        self.mock = mock if mock is not None else SETTINGS.LLM_MOCK
        self.input_price = SETTINGS.LLM_INPUT_PRICE_PER_1M
        self.output_price = SETTINGS.LLM_OUTPUT_PRICE_PER_1M

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        response_format: dict[str, str] | None = None,
    ) -> LLMResult:
        if self.mock:
            return self._mock_chat(messages, temperature, max_tokens, response_format)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        last_exception: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await self._request(payload)
            except (
                LLMRateLimitError,
                LLMTimeoutError,
                httpx.NetworkError,
                httpx.ConnectError,
            ) as exc:
                last_exception = exc
                if attempt >= self.max_retries:
                    break
                wait = self.retry_backoff**attempt
                await asyncio.sleep(wait)
            except LLMError:
                raise
            except Exception as exc:
                raise LLMUnknownError(
                    str(exc), details={"type": type(exc).__name__}
                ) from exc

        raise last_exception or LLMUnknownError("LLM request failed after retries")

    async def _request(self, payload: dict[str, Any]) -> LLMResult:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        start = time.time()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(
                    f"LLM request timed out after {self.timeout}s"
                ) from exc
            except (httpx.NetworkError, httpx.ConnectError) as exc:
                raise LLMTimeoutError(f"LLM network error: {exc}") from exc

        latency_ms = (time.time() - start) * 1000

        if resp.status_code == 429:
            raise LLMRateLimitError(
                "LLM rate limit exceeded",
                status_code=resp.status_code,
                details=resp.text,
            )
        if resp.status_code == 400:
            error_body = self._safe_json(resp)
            if self._is_content_filter_error(error_body):
                raise LLMContentFilterError(
                    "LLM content filter triggered",
                    status_code=resp.status_code,
                    details=error_body,
                )
        if resp.status_code >= 500:
            raise LLMRateLimitError(
                f"LLM server error {resp.status_code}",
                status_code=resp.status_code,
                details=resp.text,
            )

        if resp.status_code >= 400:
            raise LLMUnknownError(
                f"LLM HTTP error {resp.status_code}",
                status_code=resp.status_code,
                details=resp.text,
            )

        data = resp.json()
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0) or 0
        completion_tokens = usage.get("completion_tokens", 0) or 0
        total_tokens = usage.get("total_tokens", 0) or (
            prompt_tokens + completion_tokens
        )

        cost_usd = self._estimate_cost(prompt_tokens, completion_tokens)

        return LLMResult(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            model=data.get("model", self.model),
            raw_response=data,
        )

    @staticmethod
    def _safe_json(resp: httpx.Response) -> Any:
        try:
            return resp.json()
        except Exception:
            return resp.text

    @staticmethod
    def _is_content_filter_error(error_body: Any) -> bool:
        if not isinstance(error_body, dict):
            return False
        error = error_body.get("error", {})
        code = (error.get("code") or "").lower()
        message = (error.get("message") or "").lower()
        return (
            "content_filter" in code
            or "content filter" in message
            or "safety" in message
        )

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return prompt_tokens * (self.input_price / 1_000_000) + completion_tokens * (
            self.output_price / 1_000_000
        )

    def _mock_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: dict[str, str] | None = None,
    ) -> LLMResult:
        last = messages[-1]["content"][:120]
        user_text = messages[-1]["content"].lower()
        is_title_request = "标题" in user_text or "titles" in user_text

        if (
            response_format
            and response_format.get("type") == "json_object"
            and is_title_request
        ):
            content = json.dumps(
                {
                    "titles": [
                        f"{last[:20]}爆款标题一",
                        f"{last[:20]}爆款标题二",
                        f"{last[:20]}爆款标题三",
                    ]
                }
            )
        elif response_format and response_format.get("type") == "json_object":
            content = json.dumps({"mock": True, "reply": f"收到问题：{last}"})
        else:
            content = (
                f"【模拟 LLM 回答】收到问题：{last}... "
                f"这是一个基于本地 mock 的示例回复"
                f"（temperature={temperature}, max_tokens={max_tokens}）。"
            )
        prompt_tokens = sum(len(m["content"]) // 4 for m in messages)
        completion_tokens = len(content) // 4
        total_tokens = prompt_tokens + completion_tokens
        return LLMResult(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=100.0,
            cost_usd=0.0,
            model=self.model,
            raw_response={"mock": True},
        )

    async def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """请求模型返回 JSON 并自动解析。"""
        result = await self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(result.content)
        except json.JSONDecodeError as exc:
            raise LLMUnknownError(
                f"LLM returned invalid JSON: {result.content[:200]}"
            ) from exc
