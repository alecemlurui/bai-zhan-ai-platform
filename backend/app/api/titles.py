"""
api/titles.py

标题生成与选择 API。
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_active_user
from ..models import Task, User
from ..schemas import TaskResponse, TitleResponse
from ..services.topic import list_titles, select_title
from ..tasks import run_agent_task

router = APIRouter(prefix="/api/v1/topics", tags=["titles"])


@router.post("/{topic_id}/generate-titles", response_model=TaskResponse)
async def generate_titles(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
):
    task = await Task.create(
        type="generate_titles",
        payload={"topic_id": topic_id},
    )
    run_agent_task.delay(task.id)
    return task


@router.get("/{topic_id}/titles", response_model=list[TitleResponse])
async def get_titles(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
):
    return await list_titles(topic_id)


@router.post("/titles/{title_id}/select", response_model=TitleResponse)
async def choose_title(
    title_id: int,
    current_user: User = Depends(get_current_active_user),
):
    try:
        return await select_title(title_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Title not found")
