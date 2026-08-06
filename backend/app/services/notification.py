import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundException, AuthException
from app.models.communication import Notification, Announcement
from app.schemas.dashboard import NotificationCreate, AnnouncementCreate

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Enterprise Notification Service managing alerts, unread counts, bulk reads, and archiving.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def dispatch_notification(
        self,
        user_id: UUID,
        title: str,
        content: str,
        priority: str = "medium",
        category: str = "general",
        notification_type: str = "system",
        link: Optional[str] = None
    ) -> Notification:
        """Dispatches a new notification to a specific user."""
        notif = Notification(
            user_id=user_id,
            title=title,
            content=content,
            priority=priority,
            category=category,
            notification_type=notification_type,
            link=link,
            is_read=False,
            is_archived=False
        )
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def get_user_notifications(
        self,
        user_id: UUID,
        category: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Fetches notifications for a user."""
        stmt = select(Notification).filter(Notification.user_id == user_id, Notification.is_deleted == False, Notification.is_archived == False)
        if category:
            stmt = stmt.filter(Notification.category == category)
        if unread_only:
            stmt = stmt.filter(Notification.is_read == False)

        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def count_unread(self, user_id: UUID) -> int:
        """Returns total unread notifications count for a user."""
        stmt = select(func.count(Notification.id)).filter(Notification.user_id == user_id, Notification.is_read == False, Notification.is_deleted == False)
        res = await self.db.execute(stmt)
        return res.scalar() or 0

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Notification:
        """Marks a single notification as read."""
        stmt = select(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id)
        res = await self.db.execute(stmt)
        notif = res.scalars().first()
        if not notif:
            raise EntityNotFoundException("Notification not found.")

        notif.is_read = True
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Bulk marks all unread notifications as read for a user."""
        stmt = update(Notification).where(Notification.user_id == user_id, Notification.is_read == False).values(is_read=True)
        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount

    async def archive_notification(self, notification_id: UUID, user_id: UUID) -> Notification:
        """Archives a notification."""
        stmt = select(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id)
        res = await self.db.execute(stmt)
        notif = res.scalars().first()
        if not notif:
            raise EntityNotFoundException("Notification not found.")

        notif.is_archived = True
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> None:
        """Soft deletes a notification."""
        stmt = select(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id)
        res = await self.db.execute(stmt)
        notif = res.scalars().first()
        if notnotif:
            raise EntityNotFoundException("Notification not found.")

        notif.is_deleted = True
        self.db.add(notif)
        await self.db.commit()


class AnnouncementService:
    """
    Manages course-wide, department-wide, and global platform announcements.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_announcement(self, creator_id: UUID, payload: AnnouncementCreate) -> Announcement:
        """Creates and broadcasts an announcement."""
        anc = Announcement(
            title=payload.title,
            content=payload.content,
            target_type=payload.target_type,
            course_id=payload.course_id,
            classroom_id=payload.classroom_id,
            department=payload.department,
            creator_id=creator_id
        )
        self.db.add(anc)
        await self.db.commit()
        await self.db.refresh(anc)
        return anc

    async def get_announcements(
        self,
        course_id: Optional[UUID] = None,
        department: Optional[str] = None
    ) -> List[Announcement]:
        """Lists active announcements filtered by course or scope."""
        stmt = select(Announcement).filter(Announcement.is_deleted == False)
        if course_id:
            stmt = stmt.filter(Announcement.course_id == course_id)
        elif department:
            stmt = stmt.filter(Announcement.department == department)

        stmt = stmt.order_by(Announcement.created_at.desc())
        res = await self.db.execute(stmt)
        return res.scalars().all()
