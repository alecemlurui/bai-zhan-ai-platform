"""
test_rag.py

RAG 分块、检索与集成测试。
默认使用 mock embedder 与 mock vector store，不依赖真实 ONNX/Chroma。
"""

import pytest

from app.services.rag import (
    build_rag_prompt_context,
    ingest_material,
    retrieve_context,
    split_text,
)


def test_split_text_basic():
    text = "a" * 500
    chunks = split_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_split_text_empty():
    assert split_text("", chunk_size=100, overlap=20) == []


@pytest.mark.asyncio
async def test_ingest_material(init_db):
    result = await ingest_material(
        material_id=1,
        text="百战智能运营平台可以帮助创作者生成爆款标题和文章。" * 10,
        metadata={"owner_id": 1},
    )
    assert result["chunks"] > 0
    assert len(result["ids"]) == result["chunks"]


@pytest.mark.asyncio
async def test_retrieve_context(init_db):
    text = "高考数学复习需要掌握函数、导数、立体几何等核心知识点。" * 10
    await ingest_material(material_id=2, text=text)
    contexts = await retrieve_context(query="高考数学复习", top_k=3)
    assert len(contexts) <= 3
    for ctx in contexts:
        assert "id" in ctx
        assert "content" in ctx
        assert "metadata" in ctx


@pytest.mark.asyncio
async def test_build_rag_prompt_context(init_db):
    text = "小红书运营技巧包括选题、封面、标题、互动等。" * 10
    await ingest_material(material_id=3, text=text)
    prompt_context = await build_rag_prompt_context(
        query="小红书运营技巧",
        top_k=2,
        max_chars=500,
    )
    assert isinstance(prompt_context, str)
    assert len(prompt_context) <= 500 + 200


@pytest.mark.asyncio
async def test_api_rag_search(client, auth_headers):
    resp = await client.get("/api/v1/rag/search?q=运营&top_k=3", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "运营"
    assert "contexts" in data


@pytest.mark.asyncio
async def test_api_rag_context(client, auth_headers):
    resp = await client.get(
        "/api/v1/rag/context?q=小红书运营&top_k=2",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "context" in data


@pytest.mark.asyncio
async def test_material_create_triggers_ingestion(client, auth_headers, monkeypatch):
    ingest_calls = []

    async def fake_ingest(material_id, text, metadata=None, collection=None):
        ingest_calls.append((material_id, text))
        return {"chunks": 1, "ids": [f"test:{material_id}:0"]}

    monkeypatch.setattr("app.api.materials.ingest_material", fake_ingest)

    resp = await client.post(
        "/api/v1/materials",
        json={"type": "text", "content": "这是一条测试素材，用于触发向量化入库。"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(ingest_calls) == 1
    assert "测试素材" in ingest_calls[0][1]


@pytest.mark.asyncio
async def test_generate_article_with_rag(client, auth_headers, monkeypatch):
    from app.services import agent_runner

    # 注入 mock 检索结果
    async def fake_retrieve(query, top_k):
        return [{"id": "chunk:1:0", "content": "RAG 测试上下文"}]

    monkeypatch.setattr(agent_runner, "retrieve_context", fake_retrieve)

    # 创建主题、标题
    topic_resp = await client.post(
        "/api/v1/topics",
        json={"title": "高考数学复习"},
        headers=auth_headers,
    )
    topic_id = topic_resp.json()["id"]

    title_resp = await client.post(
        f"/api/v1/topics/{topic_id}/generate-titles",
        headers=auth_headers,
    )
    task_id = title_resp.json()["id"]

    # 直接运行 AgentRunner（绕过 Celery）
    from app.models import Task

    task = await Task.get(id=task_id)
    runner = agent_runner.AgentRunner(task)
    await runner.run()

    # 选择第一个标题
    from app.models import Title

    title = await Title.filter(topic_id=topic_id).first()
    assert title is not None

    # 创建文章任务，启用 RAG
    article_task = await Task.create(
        type="generate_article",
        payload={
            "title_id": title.id,
            "use_rag": True,
            "rag_query": "高考数学复习",
            "rag_top_k": 2,
        },
    )
    runner2 = agent_runner.AgentRunner(article_task)
    await runner2.run()

    await article_task.refresh_from_db()
    assert article_task.status == "success"
    assert article_task.result is not None
    assert article_task.result["used_context_ids"]

    # 验证文章内容包含 RAG 上下文关键词
    from app.models import Article

    article = await Article.get(id=article_task.result["article_id"])
    assert "RAG" in article.content or "测试上下文" in article.content
