"""
services/topic.py

Topic / Title / Article 查询与业务逻辑。
"""

from ..models import Article, Title, Topic


async def create_topic(user, title: str, params: dict | None = None) -> Topic:
    return await Topic.create(
        user=user,
        title=title,
        params=params or {},
    )


async def list_topics(user, limit: int = 20, offset: int = 0):
    return (
        await Topic.filter(user=user)
        .order_by("-created_at")
        .offset(offset)
        .limit(limit)
        .all()
    )


async def get_topic(user, topic_id: int) -> Topic:
    return await Topic.get(user=user, id=topic_id)


async def list_titles(topic_id: int):
    return (
        await Title.filter(topic_id=topic_id)
        .order_by("-created_at")  # type: ignore[attr-defined]
        .all()
    )


async def select_title(title_id: int) -> Title:
    title = await Title.get(id=title_id)
    await Title.filter(topic_id=title.topic_id).update(  # type: ignore[attr-defined]
        is_selected=False
    )
    title.is_selected = True
    await title.save(update_fields=["is_selected"])
    return title


async def get_article(article_id: int) -> Article:
    return await Article.get(id=article_id)


async def list_articles(title_id: int):
    return await Article.filter(title_id=title_id).order_by("-created_at").all()
