"""Celery application (Redis broker). Beat fires a lightweight ``tick`` every
``SCANNER_TICK_SECONDS``; the tick decides what is due (see services/scanner.py)."""

from __future__ import annotations

from celery import Celery

from arbscan.core.config import get_settings

settings = get_settings()

celery_app = Celery("arbscan", broker=settings.redis_url, backend=settings.redis_url, include=["arbscan.workers.tasks"])
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=900,
    task_soft_time_limit=840,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "scanner-tick": {"task": "arbscan.tick", "schedule": float(settings.scanner_tick_seconds)},
        "analysis": {"task": "arbscan.analysis", "schedule": 30 * 60.0},
        "housekeeping": {"task": "arbscan.housekeeping", "schedule": 6 * 3600.0},
    },
)
