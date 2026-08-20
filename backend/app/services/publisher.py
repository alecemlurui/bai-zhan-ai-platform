"""
services/publisher.py

第三方发布适配器。提供 mock、sandbox 与真实 HTTP 发布实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from ..config import SETTINGS
from ..models import Article, PlatformAccount, PublishRecord, PublishStatus


class PublishError(Exception):
    """发布异常。"""

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.message = message
        self.details = details


class BasePublisher(ABC):
    @abstractmethod
    async def publish(
        self,
        article: Article,
        record: PublishRecord,
        account: PlatformAccount | None,
    ) -> dict[str, Any]:
        """执行发布，返回 {ext_id, status, url, ...}。"""
        raise NotImplementedError


class MockPublisher(BasePublisher):
    """Mock 发布器：直接返回成功，不调用任何外部 API。"""

    async def publish(
        self,
        article: Article,
        record: PublishRecord,
        account: PlatformAccount | None,
    ) -> dict[str, Any]:
        return {
            "platform": record.platform,
            "ext_id": f"mock-{datetime.now(timezone.utc).timestamp()}",
            "status": "success",
            "url": f"https://example.com/mock/{record.platform}/{record.id}",
            "account_id": account.id if account else None,
        }


class SandboxPublisher(BasePublisher):
    """Sandbox 发布器：模拟网络请求，记录请求/响应供审计。"""

    async def publish(
        self,
        article: Article,
        record: PublishRecord,
        account: PlatformAccount | None,
    ) -> dict[str, Any]:
        return {
            "platform": record.platform,
            "ext_id": f"sandbox-{record.id}",
            "status": "success",
            "url": f"https://sandbox.example.com/{record.platform}/{record.id}",
            "request_preview": {
                "title": article.title.text,
                "content": article.content[:200],
                "account_name": account.account_name if account else None,
            },
        }


class XiaoHongShuPublisher(BasePublisher):
    """小红书发布器。优先使用 mock/sandbox；真实 API 需补充实现。"""

    async def publish(
        self,
        article: Article,
        record: PublishRecord,
        account: PlatformAccount | None,
    ) -> dict[str, Any]:
        if SETTINGS.XIAOHONGSHU_MOCK:
            return await MockPublisher().publish(article, record, account)
        if SETTINGS.ENVIRONMENT in ("development", "staging"):
            return await SandboxPublisher().publish(article, record, account)

        # 真实调用占位：需替换为小红书开放 API
        raise PublishError(
            "Real XiaoHongShu publisher not implemented",
            details={
                "article_id": article.id,
                "account_id": account.id if account else None,
            },
        )


PUBLISHERS: dict[str, type[BasePublisher]] = {
    "xiaohongshu": XiaoHongShuPublisher,
    "mock": MockPublisher,
    "sandbox": SandboxPublisher,
}


def get_publisher(platform: str) -> BasePublisher:
    publisher_cls = PUBLISHERS.get(platform)
    if not publisher_cls:
        raise PublishError(f"Unsupported platform: {platform}")
    return publisher_cls()


async def publish_article(
    article: Article,
    platform: str,
    account: PlatformAccount | None = None,
) -> PublishRecord:
    publisher = get_publisher(platform)

    record = await PublishRecord.create(
        article=article,
        account=account,
        platform=platform,
        status=PublishStatus.PROCESSING,
    )

    try:
        result = await publisher.publish(article, record, account)
        record.status = PublishStatus.SUCCESS
        record.ext_id = result.get("ext_id")
        record.result = result
    except PublishError as exc:
        record.status = PublishStatus.FAILED
        record.error_message = exc.message
        record.result = {"error": exc.message, "details": exc.details}
    except Exception as exc:
        record.status = PublishStatus.FAILED
        record.error_message = str(exc)
        record.result = {"error": str(exc), "type": type(exc).__name__}

    await record.save()
    return record
