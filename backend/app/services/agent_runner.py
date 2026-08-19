"""
services/agent_runner.py

Agent 流程编排与状态机。
"""

from datetime import datetime, timezone
from typing import Any

from ..models import Article, ArticleStatus, Task, TaskStatus, Title, Topic
from .llm_client import LLMClient, LLMError


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

    async def _set_status(self, status: TaskStatus) -> None:
        self.task.status = status
        await self.task.save(update_fields=["status"])

    async def _set_result(self, result: dict[str, Any]) -> None:
        self.task.result = result
        await self.task.save(update_fields=["result"])

    async def run(self) -> None:
        """根据 task.type 分发执行。"""
        try:
            await self._set_status(TaskStatus.RUNNING)
            if self.task.type == "generate_titles":
                await self._generate_titles()
            elif self.task.type == "generate_article":
                await self._generate_article()
            elif self.task.type == "publish":
                await self._publish()
            else:
                raise ValueError(f"Unknown task type: {self.task.type}")
            await self._set_status(TaskStatus.SUCCESS)
        except LLMError as exc:
            await self._log(
                "Task failed due to LLM error",
                {"error": exc.message, "status_code": exc.status_code},
            )
            await self._set_status(TaskStatus.FAILED)
            raise
        except Exception as exc:
            await self._log("Task failed", {"error": str(exc)})
            await self._set_status(TaskStatus.FAILED)
            raise

    async def _generate_titles(self) -> None:
        payload = self.task.payload
        topic_id = payload["topic_id"]
        topic = await Topic.get(id=topic_id)
        count = payload.get("count", 5)

        await self._log(
            "开始生成标题", {"topic_id": topic_id, "title": topic.title, "count": count}
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是百战智能运营平台的选题助手。请根据用户给出的主题生成多个爆款标题。"
                    "标题应简短、吸引人、适合小红书/公众号风格。"
                ),
            },
            {
                "role": "user",
                "content": self._build_title_prompt(topic.title, count),
            },
        ]

        try:
            data = await self.llm.chat_json(messages)
            titles = self._parse_title_json(data, count)
        except Exception:
            # Fallback：兼容旧版纯文本输出
            result = await self.llm.chat(messages)
            titles = self._parse_title_text(result.content, count)

        created = []
        for text in titles[:count]:
            title = await Title.create(topic=topic, text=text)
            created.append({"id": title.id, "text": title.text})

        await topic.save(update_fields=["status"])
        await self._set_result(
            {
                "topic_id": topic_id,
                "titles": created,
                "count": len(created),
            }
        )
        await self._log("标题生成完成", {"count": len(created)})

    async def _generate_article(self) -> None:
        payload = self.task.payload
        title_id = payload["title_id"]
        title = await Title.get(id=title_id).prefetch_related("topic")
        rag_context = payload.get("rag_context", "")
        word_count = payload.get("word_count", 300)
        style = payload.get("style", "xiaohongshu")

        await self._log(
            "开始生成文章",
            {
                "title_id": title_id,
                "title": title.text,
                "style": style,
                "word_count": word_count,
            },
        )

        article = await Article.create(
            title=title,
            content="",
            status=ArticleStatus.GENERATING,
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是百战智能运营平台的内容创作助手。请根据标题和参考资料生成一篇社交媒体短文。"
                    "内容应自然、口语化、有吸引力，适合目标平台。"
                ),
            },
            {
                "role": "user",
                "content": self._build_article_prompt(
                    title.text,
                    title.topic.title,
                    rag_context,
                    word_count,
                    style,
                ),
            },
        ]
        result = await self.llm.chat(messages)

        article.content = result.content
        article.status = ArticleStatus.COMPLETED
        article.metadata = {
            "tokens": result.total_tokens,
            "cost_usd": round(result.cost_usd, 6),
            "latency_ms": round(result.latency_ms, 2),
            "model": result.model,
        }
        await article.save()

        await self._set_result(
            {
                "article_id": article.id,
                "title_id": title_id,
                "tokens": result.total_tokens,
                "cost_usd": round(result.cost_usd, 6),
                "latency_ms": round(result.latency_ms, 2),
                "model": result.model,
            }
        )
        await self._log("文章生成完成", {"article_id": article.id})

    async def _publish(self) -> None:
        payload = self.task.payload
        # 真实实现需调用 publisher.py
        await self._log("发布任务已接收", payload)
        await self._set_result(
            {"published": True, "platform": payload.get("platform", "xiaohongshu")}
        )

    @staticmethod
    def _build_title_prompt(topic_title: str, count: int) -> str:
        return (
            f"主题：{topic_title}\n"
            f"请生成 {count} 个标题，严格按以下 JSON 格式返回（不要包含 markdown 代码块）：\n"
            '{"titles": ["标题1", "标题2", "标题3"]}'
        )

    @staticmethod
    def _parse_title_json(data: Any, count: int) -> list[str]:
        if isinstance(data, dict):
            titles = (
                data.get("titles") or data.get("title_list") or data.get("items") or []
            )
        else:
            titles = []
        return [str(t).strip() for t in titles if str(t).strip()][:count]

    @staticmethod
    def _parse_title_text(content: str, count: int) -> list[str]:
        lines = [line.strip(" \t\r\n-•*1234567890.") for line in content.split("\n")]
        return [line for line in lines if line][:count]

    @staticmethod
    def _build_article_prompt(
        title_text: str,
        topic_title: str,
        rag_context: str,
        word_count: int,
        style: str,
    ) -> str:
        base = (
            f"标题：{title_text}\n"
            f"主题背景：{topic_title}\n"
            f"目标平台：{style}\n"
            f"字数要求：约 {word_count} 字\n"
        )
        if rag_context:
            base += f"参考资料（请优先参考并自然融入）：\n{rag_context}\n\n"
        base += (
            "请直接输出正文，不要包含标题，不要添加额外说明。"
            "内容应分段清晰，使用 emoji 增加可读性，结尾可加互动引导。"
        )
        return base
