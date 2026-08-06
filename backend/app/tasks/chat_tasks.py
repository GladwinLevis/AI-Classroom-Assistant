import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.core.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.models.communication import ChatSession, ChatMessage

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


@celery_app.task(name="app.tasks.chat_tasks.cleanup_old_chats_task")
@run_async
async def cleanup_old_chats_task(days: int = 30) -> None:
    """Soft deletes chat sessions older than specified days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    logger.info(f"Running old chat session cleanup (cutoff: {cutoff})")

    async with AsyncSessionLocal() as db:
        stmt = select(ChatSession).filter(
            ChatSession.created_at < cutoff, 
            ChatSession.is_deleted == False,
            ChatSession.is_pinned == False
        )
        res = await db.execute(stmt)
        sessions = res.scalars().all()
        
        for s in sessions:
            s.is_deleted = True
            db.add(s)
            
        await db.commit()
        logger.info(f"Soft deleted {len(sessions)} inactive chat sessions.")


@celery_app.task(name="app.tasks.chat_tasks.chat_analytics_task")
@run_async
async def chat_analytics_task() -> None:
    """Calculates daily chat analytics: total tokens, average latency."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    logger.info("Computing daily chatbot analytics...")

    async with AsyncSessionLocal() as db:
        stmt = select(ChatMessage).filter(
            ChatMessage.created_at >= cutoff,
            ChatMessage.sender == "assistant"
        )
        res = await db.execute(stmt)
        msgs = res.scalars().all()
        
        if not msgs:
            logger.info("No messages found in the last 24 hours to analyze.")
            return
            
        total_prompt_tokens = sum(m.tokens_prompt or 0 for m in msgs)
        total_resp_tokens = sum(m.tokens_response or 0 for m in msgs)
        avg_latency = sum(m.latency_ms or 0 for m in msgs) / len(msgs)

        logger.info(
            f"Daily Chatbot Analytics:\n"
            f"- Total Messages: {len(msgs)}\n"
            f"- Prompt Tokens: {total_prompt_tokens}\n"
            f"- Response Tokens: {total_resp_tokens}\n"
            f"- Average Latency: {avg_latency:.2f}ms"
        )
