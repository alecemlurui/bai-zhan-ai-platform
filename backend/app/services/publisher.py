"""
services/publisher.py

第三方发布适配器。当前为 mock 实现，保留真实接口接入点。
"""

from datetime import datetime, timezone
from typing import Any

from ..config import SETTINGS
from ..models import Article, PublishRecord, PublishStatus


class BasePublisher:
    async def publish(self, article: Article, record: PublishRecord) -> dict[str, Any]:
        raise NotImplementedError


class XiaoHongShuPublisher(BasePublisher):
    async def publish(self, article: Article, record: PublishRecord) -> dict[str, Any]:
        if SETTINGS.XIAOHONGSHU_MOCK:
            return {
                "platform": "xiaohongshu",
                "ext_id": f"mock-{datetime.now(timezone.utc).timestamp()}",
                "status": "success",
                "url": "https://www.xiaohongshu.com/mock",
            }

        # 真实调用占位
        raise NotImplementedError("Real XiaoHongShu publisher not implemented")


PUBLISHERS = {
    "xiaohongshu": XiaoHongShuPublisher,
}


async def publish_article(article: Article, platform: str) -> PublishRecord:
    publisher_cls = PUBLISHERS.get(platform)
    if not publisher_cls:
        raise ValueError(f"Unsupported platform: {platform}")

    record = await PublishRecord.create(
        article=article,
        platform=platform,
        status=PublishStatus.PROCESSING,
    )

    try:
        result = await publisher_cls().publish(article, record)
        record.status = PublishStatus.SUCCESS
        record.ext_id = result.get("ext_id")
        record.result = result
    except Exception as exc:
        record.status = PublishStatus.FAILED
        record.error_message = str(exc)

    await record.save()
    return record
