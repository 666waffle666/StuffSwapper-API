from celery import Celery
from .config import Config
from datetime import timezone

celery_app = Celery(
    "stuffswapper",
    broker=f"{Config.REDIS_URL}/0",
    backend=f"{Config.REDIS_URL}/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=timezone.utc,
    enable_utc=True,
    worker_concurrency=4,
    task_soft_time_limit=30,
    task_time_limit=60,
)
