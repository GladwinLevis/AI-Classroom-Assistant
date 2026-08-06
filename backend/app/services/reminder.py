import logging
import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_calendar import SmartReminder
from app.schemas.advanced import SmartReminderCreate, SmartReminderResponse

logger = logging.getLogger(__name__)


class SmartReminderService:
    """
    Smart Automated Reminder Engine managing alerts for low attendance, assignments, and study milestones.
    Queries user reminders directly from database records.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reminder(self, user_id: uuid.UUID, payload: SmartReminderCreate) -> SmartReminderResponse:
        """Creates a new automated smart reminder."""
        reminder = SmartReminder(
            user_id=user_id,
            title=payload.title,
            reminder_type=payload.reminder_type,
            remind_at=payload.remind_at,
            is_triggered=False
        )
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)

        return SmartReminderResponse.model_validate(reminder)

    async def list_active_reminders(self, user_id: uuid.UUID) -> List[SmartReminderResponse]:
        """Retrieves active user smart reminders."""
        stmt = select(SmartReminder).filter(
            SmartReminder.user_id == user_id,
            SmartReminder.is_triggered == False,
            SmartReminder.is_deleted == False
        ).order_by(SmartReminder.remind_at.asc())
        res = await self.db.execute(stmt)
        reminders = res.scalars().all()

        return [SmartReminderResponse.model_validate(r) for r in reminders]
