import logging
import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic_calendar import CalendarEvent
from app.schemas.advanced import CalendarEventCreate, CalendarEventResponse

logger = logging.getLogger(__name__)


class CalendarService:
    """
    Academic Calendar Service managing study events, assignment deadlines, and exam countdowns.
    Queries user calendar entries directly from the database.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(self, user_id: uuid.UUID, payload: CalendarEventCreate) -> CalendarEventResponse:
        """Schedules a new calendar event."""
        event = CalendarEvent(
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            event_type=payload.event_type,
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_completed=False
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        return CalendarEventResponse.model_validate(event)

    async def list_events(self, user_id: uuid.UUID) -> List[CalendarEventResponse]:
        """Lists user academic calendar events."""
        stmt = select(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.is_deleted == False
        ).order_by(CalendarEvent.start_time.asc())
        res = await self.db.execute(stmt)
        events = res.scalars().all()

        return [CalendarEventResponse.model_validate(e) for e in events]
