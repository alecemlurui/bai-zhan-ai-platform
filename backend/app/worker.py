"""
worker.py

Celery worker 配置。
"""

from celery import Celery

from .config import CELERY_CONFIG

app = Celery("bai_zhan_worker")
app.conf.update(CELERY_CONFIG)

# 自动发现任务
app.autodiscover_tasks(["app"])
