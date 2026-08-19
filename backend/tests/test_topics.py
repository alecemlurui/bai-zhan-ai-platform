"""
test_topics.py
"""

import pytest


@pytest.mark.asyncio
async def test_create_topic(client, auth_headers):
    resp = await client.post(
        "/api/v1/topics",
        json={"title": "高考数学复习", "params": {"style": "xiaohongshu"}},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "高考数学复习"
    assert data["user_id"] is not None


@pytest.mark.asyncio
async def test_list_topics(client, auth_headers):
    await client.post(
        "/api/v1/topics",
        json={"title": "Topic A"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/topics", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_topic_unauthorized(client):
    resp = await client.post("/api/v1/topics", json={"title": "test"})
    assert resp.status_code == 401
