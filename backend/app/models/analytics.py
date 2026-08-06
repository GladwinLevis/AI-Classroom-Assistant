import uuid
from datetime import date
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class ActivityLog(BaseModel):
    """
    SQLAlchemy Model representing basic user activity logs (e.g. log in, log out, view dashboard).
    """
    __tablename__ = "activity_logs"

    action: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activity_logs")


class AuditLog(BaseModel):
    """
    SQLAlchemy Model representing deep data audits for record insertions, edits, or deletes.
    Stores old values and new values in JSON formats.
    """
    __tablename__ = "audit_logs"

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # insert, update, delete
    table_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    
    old_values: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")


class DashboardAnalytics(BaseModel):
    """
    SQLAlchemy Model storing pre-aggregated analytics metrics for fast dashboard rendering.
    """
    __tablename__ = "dashboard_analytics"

    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(nullable=False)
    date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)  # Context data for graph rendering
