"""
api/tasks.py

任务状态查询 API。
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_active_user
from ..models import Task, User
from ..schemas import TaskResponse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskResponse)
async def detail(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
):
    task = await Task.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
