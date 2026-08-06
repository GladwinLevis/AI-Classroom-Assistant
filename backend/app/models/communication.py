import uuid
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, Boolean, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class ChatSession(BaseModel):
    """
    SQLAlchemy Model representing chatbot sessions opened by users.
    """
    __tablename__ = "chat_sessions"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class ChatMessage(BaseModel):
    """
    SQLAlchemy Model representing individual messages inside chatbot sessions.
    """
    __tablename__ = "chat_messages"

    sender: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user' or 'assistant'
    message_text: Mapped[str] = mapped_column(Text(), nullable=False)
    tokens_prompt: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_response: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    citations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    session: Mapped[ChatSession] = relationship(ChatSession, back_populates="messages")


class Notification(BaseModel):
    """
    SQLAlchemy Model representing alerts, messages, and platform notifications for users.
    """
    __tablename__ = "notifications"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # low, medium, high, urgent
    category: Mapped[str] = mapped_column(String(50), default="general", nullable=False)  # attendance, assignment, quiz, system, announcement
    notification_type: Mapped[str] = mapped_column(String(50), default="system", nullable=False)
    link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")


class Announcement(BaseModel):
    """
    SQLAlchemy Model representing announcements broadcasted to specific classes or school-wide.
    """
    __tablename__ = "announcements"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), default="course", nullable=False)  # course, classroom, department, global
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    classroom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    course: Mapped[Optional["Course"]] = relationship("Course", back_populates="announcements")
    creator: Mapped["User"] = relationship("User", back_populates="announcements")
