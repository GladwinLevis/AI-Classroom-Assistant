import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class CalendarEvent(BaseModel):
    """
    SQLAlchemy Model representing study calendar events, assignment deadlines, and exam countdowns.
    """
    __tablename__ = "calendar_events"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), default="study", nullable=False)  # study, assignment, quiz, exam_countdown, revision
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")


class SmartReminder(BaseModel):
    """
    SQLAlchemy Model representing automated reminders for assignments, low attendance, and quizzes.
    """
    __tablename__ = "smart_reminders"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reminder_type: Mapped[str] = mapped_column(String(50), default="study_goal", nullable=False)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
