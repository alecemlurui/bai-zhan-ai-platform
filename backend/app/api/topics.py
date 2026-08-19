"""
api/topics.py

主题相关 API。
"""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_active_user
from ..models import User
from ..schemas import TopicCreateRequest, TopicResponse
from ..services.topic import create_topic, get_topic, list_topics

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])


@router.post("", response_model=TopicResponse)
async def create(
    payload: TopicCreateRequest,
    current_user: User = Depends(get_current_active_user),
):
    return await create_topic(current_user, payload.title, payload.params)


@router.get("", response_model=list[TopicResponse])
async def list_all(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
):
    return await list_topics(current_user, limit, offset)


@router.get("/{topic_id}", response_model=TopicResponse)
async def detail(topic_id: int, current_user: User = Depends(get_current_active_user)):
    try:
        return await get_topic(current_user, topic_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Topic not found")
