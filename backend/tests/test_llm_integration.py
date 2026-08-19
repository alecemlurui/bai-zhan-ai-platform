"""
test_llm_integration.py

LLM 客户端与 Agent Runner 集成测试。
覆盖 mock 模式、真实调用模拟、重试、异常、JSON 解析。
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.models import Task, Topic, User
from app.services.agent_runner import AgentRunner
from app.services.llm_client import (
    LLMClient,
    LLMContentFilterError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnknownError,
)


@pytest.mark.asyncio
async def test_llm_mock_chat():
    client = LLMClient(mock=True, model="deepseek-chat")
    messages = [{"role": "user", "content": "hello" * 10}]
    result = await client.chat(messages, temperature=0.5, max_tokens=100)

    assert result.content.startswith("【模拟 LLM 回答】")
    assert result.model == "deepseek-chat"
    assert result.total_tokens >= 0
    assert result.latency_ms >= 0
    assert result.cost_usd == 0.0


@pytest.mark.asyncio
async def test_llm_mock_chat_json():
    client = LLMClient(mock=True)
    messages = [{"role": "user", "content": "test"}]
    data = await client.chat_json(messages)

    assert isinstance(data, dict)
    assert data.get("mock") is True


@pytest.mark.asyncio
async def test_llm_real_chat_success():
    fake_response = {
        "id": "chatcmpl-test",
        "model": "deepseek-chat",
        "choices": [
            {
                "message": {"role": "assistant", "content": "Hello, world!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }

    mock_resp = httpx.Response(200, json=fake_response)

    client = LLMClient(api_key="fake-key", base_url="https://fake.com", mock=False)

    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp
    ):
        result = await client.chat([{"role": "user", "content": "hi"}])

    assert result.content == "Hello, world!"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 5
    assert result.total_tokens == 15
    assert result.model == "deepseek-chat"
    assert result.cost_usd >= 0


@pytest.mark.asyncio
async def test_llm_retry_on_429_then_success():
    fake_response = {
        "id": "chatcmpl-test",
        "model": "deepseek-chat",
        "choices": [{"message": {"role": "assistant", "content": "OK"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    success_resp = httpx.Response(200, json=fake_response)
    rate_resp = httpx.Response(429, text="rate limited")

    client = LLMClient(
        api_key="fake-key",
        base_url="https://fake.com",
        mock=False,
        max_retries=2,
        retry_backoff=1.0,
    )

    call_count = 0

    async def fake_post(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return rate_resp
        return success_resp

    with patch("httpx.AsyncClient.post", side_effect=fake_post):
        result = await client.chat([{"role": "user", "content": "hi"}])

    assert result.content == "OK"
    assert call_count == 2


@pytest.mark.asyncio
async def test_llm_retry_exhausted_on_429():
    rate_resp = httpx.Response(429, text="rate limited")
    client = LLMClient(
        api_key="fake-key",
        base_url="https://fake.com",
        mock=False,
        max_retries=2,
        retry_backoff=1.0,
    )

    with patch(
        "httpx.AsyncClient.post", new_callable=AsyncMock, return_value=rate_resp
    ):
        with pytest.raises(LLMRateLimitError):
            await client.chat([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_llm_content_filter_error():
    fake_response = {
        "error": {
            "code": "content_filter_triggered",
            "message": "The response was filtered due to safety reasons.",
        }
    }
    resp = httpx.Response(400, json=fake_response)
    client = LLMClient(api_key="fake-key", base_url="https://fake.com", mock=False)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=resp):
        with pytest.raises(LLMContentFilterError):
            await client.chat([{"role": "user", "content": "bad"}])


@pytest.mark.asyncio
async def test_llm_timeout_error():
    client = LLMClient(
        api_key="fake-key", base_url="https://fake.com", mock=False, timeout=1
    )

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(LLMTimeoutError):
            await client.chat([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_llm_unknown_error():
    client = LLMClient(api_key="fake-key", base_url="https://fake.com", mock=False)

    with patch("httpx.AsyncClient.post", side_effect=ValueError("boom")):
        with pytest.raises(LLMUnknownError):
            await client.chat([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_agent_runner_generate_titles(init_db):
    user = await User.create(username="agent_test", password_hash="hash")
    topic = await Topic.create(user=user, title="高考数学复习")
    task = await Task.create(
        type="generate_titles",
        payload={"topic_id": topic.id, "count": 3},
    )
    runner = AgentRunner(task)
    await runner.run()

    await task.refresh_from_db()
    assert task.status == "success"
    assert task.result is not None
    assert len(task.result["titles"]) == 3
    for t in task.result["titles"]:
        assert "id" in t
        assert "text" in t
        assert t["text"]


@pytest.mark.asyncio
async def test_agent_runner_generate_article(init_db):
    user = await User.create(username="agent_test2", password_hash="hash")
    topic = await Topic.create(user=user, title="考研英语写作")
    from app.models import Title

    title = await Title.create(topic=topic, text="考研英语写作三大技巧")
    task = await Task.create(
        type="generate_article",
        payload={"title_id": title.id, "word_count": 200, "style": "xiaohongshu"},
    )
    runner = AgentRunner(task)
    await runner.run()

    await task.refresh_from_db()
    assert task.status == "success"
    assert task.result is not None
    assert task.result["article_id"]
    assert task.result["tokens"] >= 0
