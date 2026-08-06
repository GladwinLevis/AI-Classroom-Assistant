import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


def utc_now() -> datetime:
    """Helper to return current time with UTC timezone info."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base for 2.0 type annotated models.
    """
    pass


class TimestampMixin:
    """Mixin class adding standard created_at and updated_at timestamp columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin class adding soft-delete columns and support flags."""
    is_deleted: Mapped[bool] = mapped_column(
        Boolean(),
        default=False,
        nullable=False,
        index=True
    )
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True
    )


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """
    Abstract BaseModel declaring UUID primary key and soft-delete/timestamps mixins.
    """
    __abstract__ = True

    @declared_attr
    def __tablename__(cls) -> str:
        # Defaults table name to lowercase version of class name + 's'
        return cls.__name__.lower() + "s"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False
    )
