import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Path, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import (
    NotificationResponse,
    AnnouncementCreate,
    AnnouncementResponse
)
from app.services.notification import NotificationService, AnnouncementService

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------------------
# NOTIFICATION ENDPOINTS
# ------------------------------------------------------------------------------

@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    category: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves notifications for the current user."""
    svc = NotificationService(db)
    return await svc.get_user_notifications(current_user.id, category, unread_only)


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns unread notification count for the current user."""
    svc = NotificationService(db)
    count = await svc.count_unread(current_user.id)
    return {"unread_count": count}


@router.post("/{id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Marks a single notification as read."""
    svc = NotificationService(db)
    return await svc.mark_as_read(id, current_user.id)


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk marks all unread notifications as read for the current user."""
    svc = NotificationService(db)
    count = await svc.mark_all_as_read(current_user.id)
    return {"success": True, "updated_count": count}


@router.post("/{id}/archive", response_model=NotificationResponse)
async def archive_notification(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Archives a notification."""
    svc = NotificationService(db)
    return await svc.archive_notification(id, current_user.id)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    id: UUID = Path(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Deletes a notification."""
    svc = NotificationService(db)
    await svc.delete_notification(id, current_user.id)
    return {"success": True, "message": "Notification deleted successfully."}


# ------------------------------------------------------------------------------
# ANNOUNCEMENT ENDPOINTS
# ------------------------------------------------------------------------------

@router.post("/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    payload: AnnouncementCreate = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates and broadcasts an announcement."""
    svc = AnnouncementService(db)
    return await svc.create_announcement(current_user.id, payload)


@router.get("/announcements", response_model=List[AnnouncementResponse])
async def list_announcements(
    course_id: Optional[UUID] = Query(None),
    department: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists announcements filtered by course or scope."""
    svc = AnnouncementService(db)
    return await svc.get_announcements(course_id, department)
