"""
api/articles.py

文章生成 API。
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_active_user
from ..models import Task, User
from ..schemas import ArticleCreateRequest, ArticleResponse, TaskResponse
from ..services.topic import get_article, list_articles
from ..tasks import run_agent_task

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


@router.post("/generate", response_model=TaskResponse)
async def generate(
    payload: ArticleCreateRequest,
    current_user: User = Depends(get_current_active_user),
):
    task_payload: dict[str, Any] = {"title_id": payload.title_id}
    if payload.use_rag:
        task_payload["use_rag"] = True
        task_payload["rag_query"] = payload.rag_query or ""
        task_payload["rag_top_k"] = payload.rag_top_k or 5
    task = await Task.create(
        type="generate_article",
        payload=task_payload,
    )
    run_agent_task.delay(task.id)
    return task


@router.get("/title/{title_id}", response_model=list[ArticleResponse])
async def get_by_title(
    title_id: int,
    current_user: User = Depends(get_current_active_user),
):
    return await list_articles(title_id)


@router.get("/{article_id}", response_model=ArticleResponse)
async def detail(
    article_id: int,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await get_article(article_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Article not found")
