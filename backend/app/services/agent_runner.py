"""
services/agent_runner.py

Agent 流程编排与状态机。
"""

import time
from datetime import datetime, timezone
from typing import Any

from ..models import Article, Task, Topic, Title
from .llm_client import LLMClient


class AgentRunner:
    def __init__(self, task: Task):
        self.task = task
        self.llm = LLMClient()

    async def _log(self, message: str, data: dict[str, Any] | None = None) -> None:
        log_entry = {
            "time": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "data": data or {},
        }
        self.task.logs = self.task.logs or []
        self.task.logs.append(log_entry)
        await self.task.save(update_fields=["logs"])

    async def _set_status(self, status: str) -> None:
        self.task.status = status
        await self.task.save(update_fields=["status"])

    async def _set_result(self, result: dict[str, Any]) -> None:
        self.task.result = result
        await self.task.save(update_fields=["result"])

    async def run(self) -> None:
        """根据 task.type 分发执行。"""
        try:
            await self._set_status("running")
            if self.task.type == "generate_titles":
                await self._generate_titles()
            elif self.task.type == "generate_article":
                await self._generate_article()
            elif self.task.type == "publish":
                await self._publish()
            else:
                raise ValueError(f"Unknown task type: {self.task.type}")
            await self._set_status("success")
        except Exception as exc:
            await self._log("Task failed", {"error": str(exc)})
            await self._set_status("failed")
            raise

    async def _generate_titles(self) -> None:
        payload = self.task.payload
        topic_id = payload["topic_id"]
        topic = await Topic.get(id=topic_id)

        await self._log("开始生成标题", {"topic_id": topic_id, "title": topic.title})

        messages = [
            {
                "role": "system",
                "content": "你是百战智能运营平台的选题助手。请根据主题生成 5 个吸引人的标题。",
            },
            {
                "role": "user",
                "content": f"主题：{topic.title}\n请生成 5 个标题，每行一个，不要编号。",
            },
        ]
        result = await self.llm.chat(messages)
        titles = [line.strip() for line in result.content.split("\n") if line.strip()]

        created = []
        for text in titles[:5]:
            title = await Title.create(topic=topic, text=text)
            created.append({"id": title.id, "text": title.text})

        await topic.save(update_fields=["status"])
        await self._set_result(
            {
                "topic_id": topic_id,
                "titles": created,
                "tokens": result.total_tokens,
                "latency_ms": result.latency_ms,
            }
        )
        await self._log("标题生成完成", {"count": len(created)})

    async def _generate_article(self) -> None:
        payload = self.task.payload
        title_id = payload["title_id"]
        title = await Title.get(id=title_id).prefetch_related("topic")

        await self._log("开始生成文章", {"title_id": title_id, "title": title.text})

        article = await Article.create(
            title=title,
            content="",
            status="generating",
        )

        messages = [
            {
                "role": "system",
                "content": "你是百战智能运营平台的内容创作助手。请根据标题生成一篇小红书风格的短文。",
            },
            {
                "role": "user",
                "content": f"标题：{title.text}\n主题背景：{title.topic.title}\n请生成一篇 300 字左右、适合小红书风格的短文。",
            },
        ]
        result = await self.llm.chat(messages)

        article.content = result.content
        article.status = "completed"
        article.metadata = {
            "tokens": result.total_tokens,
            "latency_ms": result.latency_ms,
        }
        await article.save()

        await self._set_result(
            {
                "article_id": article.id,
                "title_id": title_id,
                "tokens": result.total_tokens,
                "latency_ms": result.latency_ms,
            }
        )
        await self._log("文章生成完成", {"article_id": article.id})

    async def _publish(self) -> None:
        payload = self.task.payload
        # 真实实现需调用 publisher.py
        await self._log("发布任务已接收", payload)
        await self._set_result({"published": True, "platform": payload.get("platform", "xiaohongshu")})
