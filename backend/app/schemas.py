"""
schemas.py

Pydantic 请求/响应模型。
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None


class UserLoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TopicCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    params: Optional[dict[str, Any]] = Field(default_factory=dict)


class TopicResponse(BaseModel):
    id: int
    user_id: int
    title: str
    params: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TitleResponse(BaseModel):
    id: int
    topic_id: int
    text: str
    score: Optional[float]
    is_selected: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleCreateRequest(BaseModel):
    title_id: int
    use_rag: bool = False
    rag_query: str | None = None
    rag_top_k: int | None = None


class ArticleCoverRequest(BaseModel):
    article_id: int
    prompt: str
    width: int = 512
    height: int = 512


class ArticleResponse(BaseModel):
    id: int
    title_id: int
    content: str
    status: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskResponse(BaseModel):
    id: int
    type: str
    status: str
    attempts: int
    max_attempts: int
    result: Optional[dict[str, Any]]
    logs: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PublishRequest(BaseModel):
    article_id: int
    platform: str = "xiaohongshu"
    account_id: Optional[int] = None


class PublishRecordResponse(BaseModel):
    id: int
    article_id: int
    account_id: Optional[int]
    platform: str
    status: str
    ext_id: Optional[str]
    error_message: Optional[str]
    result: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlatformAccountCreateRequest(BaseModel):
    platform: str = Field(..., pattern="^(xiaohongshu|weibo|douyin)$")
    account_name: str = Field(..., min_length=1, max_length=256)
    credentials: dict[str, Any] = Field(default_factory=dict)


class PlatformAccountResponse(BaseModel):
    id: int
    owner_id: int
    platform: str
    account_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialCreateRequest(BaseModel):
    type: str = Field(..., pattern="^(text|image)$")
    content: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[list[str]] = Field(default_factory=list)


class MaterialResponse(BaseModel):
    id: int
    owner_id: int
    type: str
    content: Optional[str]
    url: Optional[str]
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
