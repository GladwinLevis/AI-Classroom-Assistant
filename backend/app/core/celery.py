from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_classroom_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # In development/test mode, run tasks synchronously
    task_always_eager=True,
    task_eager_propagates=True
)

# Autodiscover tasks from app.tasks package
celery_app.autodiscover_tasks(["app.tasks"])
