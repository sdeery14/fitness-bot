"""Celery application configuration."""
from celery import Celery

from src.config import settings

# Create Celery app with proper broker and backend URLs
broker_url = settings.CELERY_BROKER_URL if settings.CELERY_BROKER_URL else settings.REDIS_URL
backend_url = settings.CELERY_RESULT_BACKEND if settings.CELERY_RESULT_BACKEND else settings.REDIS_URL

celery_app = Celery(
    "fitness_bot",
    broker=broker_url,
    backend=backend_url,
    include=[
        "src.workers.plan_generation",
        "src.workers.notifications",
        "src.workers.schedule_recalc",
        "src.workers.phase_transitions",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
)

# Task routing
celery_app.conf.task_routes = {
    "src.workers.plan_generation.*": {"queue": "plan_generation"},
    "src.workers.notifications.*": {"queue": "notifications"},
    "src.workers.schedule_recalc.*": {"queue": "schedule"},
    "src.workers.phase_transitions.*": {"queue": "phase_transitions"},
}
