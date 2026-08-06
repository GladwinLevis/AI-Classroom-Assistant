import uuid
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class GeneratedReport(BaseModel):
    """
    SQLAlchemy Model representing exported reports (PDF, Excel, CSV).
    """
    __tablename__ = "generated_reports"

    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # student, teacher, attendance, assignment, quiz, ai_usage, course, department
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, excel, csv
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    filters: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)

    generated_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    generated_by: Mapped["User"] = relationship("User")
