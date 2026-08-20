"""
router.py

API 路由聚合。
"""

from fastapi import APIRouter

from .api import (
    accounts,
    articles,
    auth,
    health,
    materials,
    media,
    publish,
    rag,
    tasks,
    titles,
    topics,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(topics.router)
api_router.include_router(titles.router)
api_router.include_router(articles.router)
api_router.include_router(media.router)
api_router.include_router(materials.router)
api_router.include_router(rag.router)
api_router.include_router(tasks.router)
api_router.include_router(publish.router)
