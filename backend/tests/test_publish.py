"""
test_publish.py

小红书/第三方平台发布流程测试。
默认使用 mock publisher，不依赖真实第三方 API。
"""

import pytest

from app.models import (
    Article,
    PlatformAccount,
    PublishRecord,
    PublishStatus,
    Title,
    Topic,
    User,
)
from app.services.agent_runner import AgentRunner
from app.services.publisher import (
    MockPublisher,
    SandboxPublisher,
    get_publisher,
    publish_article,
)


@pytest.mark.asyncio
async def test_mock_publisher():
    user = await User.create(username="pub_test", password_hash="hash")
    topic = await Topic.create(user=user, title="发布测试")
    title = await Title.create(topic=topic, text="测试标题")
    article = await Article.create(title=title, content="测试内容", status="completed")

    publisher = MockPublisher()
    record = await PublishRecord.create(
        article=article,
        platform="xiaohongshu",
        status=PublishStatus.PROCESSING,
    )
    result = await publisher.publish(article, record, None)

    assert result["status"] == "success"
    assert result["ext_id"].startswith("mock-")


@pytest.mark.asyncio
async def test_sandbox_publisher():
    user = await User.create(username="pub_test2", password_hash="hash")
    topic = await Topic.create(user=user, title="Sandbox 测试")
    title = await Title.create(topic=topic, text="沙盒标题")
    article = await Article.create(title=title, content="沙盒内容", status="completed")

    publisher = SandboxPublisher()
    record = await PublishRecord.create(
        article=article,
        platform="xiaohongshu",
        status=PublishStatus.PROCESSING,
    )
    result = await publisher.publish(article, record, None)

    assert result["status"] == "success"
    assert "request_preview" in result


@pytest.mark.asyncio
async def test_publish_article_service():
    user = await User.create(username="pub_service", password_hash="hash")
    topic = await Topic.create(user=user, title="服务测试")
    title = await Title.create(topic=topic, text="服务标题")
    article = await Article.create(title=title, content="服务内容", status="completed")

    record = await publish_article(article, "xiaohongshu")
    assert record.status == PublishStatus.SUCCESS
    assert record.ext_id is not None


@pytest.mark.asyncio
async def test_get_publisher_unsupported():
    with pytest.raises(Exception):
        get_publisher("unknown_platform")


@pytest.mark.asyncio
async def test_api_platform_account_crud(client, auth_headers):
    # Create
    resp = await client.post(
        "/api/v1/accounts",
        json={
            "platform": "xiaohongshu",
            "account_name": "我的小红书",
            "credentials": {"token": "fake"},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    account_id = resp.json()["id"]
    assert resp.json()["account_name"] == "我的小红书"

    # List
    resp = await client.get("/api/v1/accounts", headers=auth_headers)
    assert resp.status_code == 200
    assert any(a["id"] == account_id for a in resp.json())

    # Detail
    resp = await client.get(f"/api/v1/accounts/{account_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["platform"] == "xiaohongshu"

    # Delete
    resp = await client.delete(f"/api/v1/accounts/{account_id}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_api_publish_trigger(client, auth_headers):
    # 创建文章
    from app.models import User
    from app.services.topic import create_topic

    user = await User.get(username="testuser")
    topic = await create_topic(user, "高考数学复习")
    title = await Title.create(topic=topic, text="高考数学复习三大技巧")
    article = await Article.create(title=title, content="文章内容", status="completed")

    resp = await client.post(
        "/api/v1/publish",
        json={"article_id": article.id, "platform": "xiaohongshu"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "publish"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_agent_runner_publish_task(init_db):
    user = await User.create(username="agent_pub", password_hash="hash")
    topic = await Topic.create(user=user, title="Agent 发布测试")
    title = await Title.create(topic=topic, text="Agent 标题")
    article = await Article.create(
        title=title, content="Agent 内容", status="completed"
    )

    from app.models import Task

    task = await Task.create(
        type="publish",
        payload={"article_id": article.id, "platform": "xiaohongshu"},
    )
    runner = AgentRunner(task)
    await runner.run()

    await task.refresh_from_db()
    assert task.status == "success"
    assert task.result["status"] == "success"
    assert task.result["publish_record_id"] > 0

    record = await PublishRecord.get(id=task.result["publish_record_id"])
    assert record.status == PublishStatus.SUCCESS


@pytest.mark.asyncio
async def test_publish_with_account(client, auth_headers):
    from app.models import User
    from app.services.topic import create_topic

    user = await User.get(username="testuser")
    account = await PlatformAccount.create(
        owner=user,
        platform="xiaohongshu",
        account_name="官方号",
        credentials={"token": "fake"},
    )
    topic = await create_topic(user, "账号发布测试")
    title = await Title.create(topic=topic, text="账号标题")
    article = await Article.create(title=title, content="内容", status="completed")

    resp = await client.post(
        "/api/v1/publish",
        json={
            "article_id": article.id,
            "platform": "xiaohongshu",
            "account_id": account.id,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "publish"
