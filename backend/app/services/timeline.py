import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import ActivityLog

logger = logging.getLogger(__name__)


class TimelineService:
    """
    Service for recording and fetching activity timeline events.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        user_id: UUID,
        action: str,
        entity_name: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> ActivityLog:
        """Logs an activity timeline event."""
        log = ActivityLog(
            user_id=user_id,
            action=action,
            entity_name=entity_name,
            entity_id=entity_id,
            ip_address=ip_address
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log

    async def get_user_timeline(self, user_id: UUID, limit: int = 20) -> List[ActivityLog]:
        """Retrieves timeline activity logs for a user."""
        stmt = select(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()
