"""Celery application configuration."""
from __future__ import annotations

from celery import Celery

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "db_explorer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    result_expires=3600,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.infrastructure"])
