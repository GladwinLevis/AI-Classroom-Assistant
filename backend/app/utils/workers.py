import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Celery
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
)


@celery_app.task(name="tasks.process_document_summary")
def process_document_summary(note_id: str, file_path: str, extension: str) -> str:
    """
    Celery task that extracts document text and generates summaries asynchronously.
    """
    logger.info(f"Background worker starting text extraction/summarization for note ID: {note_id}")
    # Async worker logic details
    return f"Finished summarization background job for note: {note_id}"


@celery_app.task(name="tasks.grade_submission_async")
def grade_submission_async(submission_id: str) -> str:
    """
    Celery task that grades submissions asynchronously.
    """
    logger.info(f"Background worker starting grading for submission ID: {submission_id}")
    # Async worker grading details
    return f"Finished grading background job for submission: {submission_id}"
