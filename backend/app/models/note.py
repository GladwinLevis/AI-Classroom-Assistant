from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Note(BaseModel):
    """
    SQLAlchemy Model representing study materials, class notes,
    and their AI-generated summaries.
    """
    __tablename__ = "notes"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)  # Path to uploaded file (local path or S3 url)
    content = Column(Text, nullable=True)            # Extracted text content
    summary = Column(Text, nullable=True)            # AI summarized points

    # Relationships
    user = relationship("User", back_populates="notes")
