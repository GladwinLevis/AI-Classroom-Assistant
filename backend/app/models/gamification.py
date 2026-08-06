import uuid
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class UserGamification(BaseModel):
    """
    SQLAlchemy Model representing student XP points, levels, streaks, badges, and achievements.
    """
    __tablename__ = "user_gamification"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    xp_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    badges: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)
    achievements: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
