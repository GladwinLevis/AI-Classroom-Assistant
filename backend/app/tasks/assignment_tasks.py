import asyncio
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.services.assignment_eval import EvaluationService

logger = logging.getLogger(__name__)


def run_async(coro):
    """Decorator helper to run async function inside sync Celery tasks."""
    import functools
    @functools.wraps(coro)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            return loop.create_task(coro(*args, **kwargs))
        else:
            return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


async def evaluate_assignment_task_async(submission_id_str: str, db: AsyncSession = None) -> None:
    """Async execution logic for assignment evaluation."""
    submission_id = UUID(submission_id_str)
    logger.info(f"Starting assignment evaluation task for submission {submission_id}")

    async def _run(session: AsyncSession):
        eval_service = EvaluationService(session)
        await eval_service.evaluate_submission(submission_id)

    if db is not None:
        await _run(db)
    else:
        async with AsyncSessionLocal() as session:
            try:
                await _run(session)
                logger.info(f"Successfully evaluated submission {submission_id}")
            except Exception as e:
                logger.exception(f"Fatal error evaluating submission {submission_id}: {str(e)}")
                await session.rollback()
                raise


@celery_app.task(name="app.tasks.assignment_tasks.evaluate_assignment_task")
@run_async
async def evaluate_assignment_task(submission_id_str: str) -> None:
    """Celery background worker entry point for evaluating student assignment submissions."""
    await evaluate_assignment_task_async(submission_id_str)
