from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.advanced import (
    CalendarEventCreate,
    CalendarEventResponse,
    SmartReminderCreate,
    SmartReminderResponse
)
from app.services.calendar_service import CalendarService
from app.services.reminder import SmartReminderService

router = APIRouter()


@router.get("/events", response_model=List[CalendarEventResponse], status_code=status.HTTP_200_OK)
async def list_calendar_events(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists user academic calendar events and exam countdowns."""
    svc = CalendarService(db)
    return await svc.list_events(current_user.id)


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_calendar_event(
    payload: CalendarEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedules a new academic study event or exam countdown."""
    svc = CalendarService(db)
    return await svc.create_event(current_user.id, payload)


@router.get("/reminders", response_model=List[SmartReminderResponse], status_code=status.HTTP_200_OK)
async def list_active_reminders(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists active smart reminders and alerts."""
    svc = SmartReminderService(db)
    return await svc.list_active_reminders(current_user.id)


@router.post("/reminders", response_model=SmartReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_smart_reminder(
    payload: SmartReminderCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new automated smart reminder."""
    svc = SmartReminderService(db)
    return await svc.create_reminder(current_user.id, payload)
