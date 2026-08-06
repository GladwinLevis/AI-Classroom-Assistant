import asyncio
import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.services.quiz_service import QuizGenerationService, LeaderboardService

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


async def generate_quiz_task_async(
    creator_id_str: str,
    notes_id_str: Optional[str] = None,
    topic: Optional[str] = None,
    num_questions: int = 5,
    difficulty: str = "mixed",
    blooms_level: Optional[List[str]] = None,
    question_types: Optional[List[str]] = None,
    course_id_str: Optional[str] = None,
    db: AsyncSession = None
) -> None:
    """Async execution logic for background quiz generation."""
    creator_id = UUID(creator_id_str)
    notes_id = UUID(notes_id_str) if notes_id_str else None
    course_id = UUID(course_id_str) if course_id_str else None

    logger.info(f"Starting background quiz generation task for creator {creator_id}")

    async def _run(session: AsyncSession):
        svc = QuizGenerationService(session)
        await svc.generate_quiz_from_source(
            creator_id=creator_id,
            notes_id=notes_id,
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            blooms_level=blooms_level,
            question_types=question_types,
            course_id=course_id
        )

    if db is not None:
        await _run(db)
    else:
        async with AsyncSessionLocal() as session:
            try:
                await _run(session)
                logger.info(f"Successfully generated quiz for creator {creator_id}")
            except Exception as e:
                logger.exception(f"Error generating quiz: {str(e)}")
                await session.rollback()
                raise


@celery_app.task(name="app.tasks.quiz_tasks.generate_quiz_task")
@run_async
async def generate_quiz_task(
    creator_id_str: str,
    notes_id_str: Optional[str] = None,
    topic: Optional[str] = None,
    num_questions: int = 5,
    difficulty: str = "mixed",
    blooms_level: Optional[List[str]] = None,
    question_types: Optional[List[str]] = None,
    course_id_str: Optional[str] = None
) -> None:
    """Celery worker entry point for AI quiz generation."""
    await generate_quiz_task_async(
        creator_id_str, notes_id_str, topic, num_questions, difficulty, blooms_level, question_types, course_id_str
    )


@celery_app.task(name="app.tasks.quiz_tasks.update_leaderboard_task")
@run_async
async def update_leaderboard_task(quiz_id_str: str) -> None:
    """Celery worker entry point for leaderboard updating."""
    quiz_id = UUID(quiz_id_str)
    async with AsyncSessionLocal() as session:
        await LeaderboardService.get_quiz_leaderboard(quiz_id, session)
