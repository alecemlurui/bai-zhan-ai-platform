"""
test_agent.py
"""

import pytest

from app.models import Task


@pytest.mark.asyncio
async def test_generate_titles_task(client, auth_headers):
    topic_resp = await client.post(
        "/api/v1/topics",
        json={"title": "考研英语写作"},
        headers=auth_headers,
    )
    topic_id = topic_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/topics/{topic_id}/generate-titles",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "generate_titles"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_agent_runner_direct(init_db):
    from app.services.agent_runner import AgentRunner

    task = await Task.create(
        type="generate_titles",
        payload={"topic_id": 1},
    )
    runner = AgentRunner(task)

    # 由于 SQLite 内存测试无真实 topic，这里仅验证初始化
    assert runner.task.id == task.id
    assert runner.llm.mock is True
