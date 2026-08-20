"""
api/publish.py

发布相关 API。
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_active_user
from ..models import Article, PlatformAccount, Task, User
from ..schemas import PublishRecordResponse, PublishRequest, TaskResponse
from ..tasks import run_agent_task

router = APIRouter(prefix="/api/v1/publish", tags=["publish"])


@router.post("", response_model=TaskResponse)
async def publish(
    payload: PublishRequest,
    current_user: User = Depends(get_current_active_user),
):
    try:
        await Article.get(id=payload.article_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Article not found")

    if payload.account_id is not None:
        try:
            account = await PlatformAccount.get(
                owner=current_user,
                id=payload.account_id,
                is_active=True,
            )
        except Exception:
            raise HTTPException(status_code=404, detail="Platform account not found")
        if account.platform != payload.platform:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Account platform mismatch: "
                    f"{account.platform} != {payload.platform}"
                ),
            )

    task = await Task.create(
        type="publish",
        payload={
            "article_id": payload.article_id,
            "platform": payload.platform,
            "account_id": payload.account_id,
        },
    )
    run_agent_task.delay(task.id)
    return task


@router.get("/article/{article_id}", response_model=list[PublishRecordResponse])
async def list_records(
    article_id: int,
    current_user: User = Depends(get_current_active_user),
):
    from ..models import PublishRecord

    return (
        await PublishRecord.filter(article_id=article_id).order_by("-created_at").all()
    )
