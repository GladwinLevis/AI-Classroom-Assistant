import asyncio
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.services.reports import ReportService

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


@celery_app.task(name="app.tasks.report_tasks.generate_report_task")
@run_async
async def generate_report_task(
    user_id_str: str,
    report_type: str,
    export_format: str,
    filters: Optional[Dict[str, Any]] = None
) -> None:
    """Celery worker task for background report file generation."""
    user_id = UUID(user_id_str)
    async with AsyncSessionLocal() as session:
        try:
            svc = ReportService(session)
            await svc.generate_report(user_id, report_type, export_format, filters)
            logger.info(f"Background report generated for user {user_id}")
        except Exception as e:
            logger.exception(f"Error in background report generation: {str(e)}")
            await session.rollback()
            raise
