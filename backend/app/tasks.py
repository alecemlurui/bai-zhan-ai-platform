"""
tasks.py

Celery 任务定义。
"""

from .worker import app as celery_app


@celery_app.task(bind=True, max_retries=3)
def run_agent_task(self, task_id: int) -> dict:
    """执行 Agent 任务。"""
    import asyncio

    from .config import TORTOISE_ORM
    from .models import Task
    from .services.agent_runner import AgentRunner

    # 初始化 Tortoise
    async def _run():
        from tortoise import Tortoise

        await Tortoise.init(config=TORTOISE_ORM)
        try:
            task = await Task.get(id=task_id)
            task.attempts += 1
            await task.save(update_fields=["attempts"])

            runner = AgentRunner(task)
            await runner.run()
            return {"task_id": task_id, "status": task.status}
        finally:
            await Tortoise.close_connections()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        # 失败重试
        raise self.retry(exc=exc, countdown=2**self.request.retries)
