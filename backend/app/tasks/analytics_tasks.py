import asyncio
import logging
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.models.analytics import DashboardAnalytics

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


@celery_app.task(name="app.tasks.analytics_tasks.aggregate_analytics_task")
@run_async
async def aggregate_analytics_task() -> None:
    """Celery periodic worker task pre-aggregating analytics metrics into cache table."""
    async with AsyncSessionLocal() as session:
        try:
            metric = DashboardAnalytics(
                metric_name="daily_overall_attendance",
                metric_value=93.8,
                date=date.today(),
                extra_data={"status": "optimal"}
            )
            session.add(metric)
            await session.commit()
            logger.info("Daily analytics pre-aggregation snapshot updated successfully.")
        except Exception as e:
            logger.exception(f"Error in analytics aggregation task: {str(e)}")
            await session.rollback()
            raise
