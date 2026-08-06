import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class RefreshToken(BaseModel):
    """
    SQLAlchemy Model storing issued Refresh Tokens.
    Used for rolling session regeneration and validation.
    """
    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class TokenBlacklist(BaseModel):
    """
    SQLAlchemy Model storing blacklisted/revoked Access Tokens (e.g. from logout).
    Checked during authentication before request completion.
    """
    __tablename__ = "token_blacklist"

    token: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
