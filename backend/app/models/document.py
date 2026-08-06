import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, Integer, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class FileUpload(BaseModel):
    """
    SQLAlchemy Model representing files uploaded to the platform storage.
    """
    __tablename__ = "file_uploads"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer(), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    uploader: Mapped["User"] = relationship("User", back_populates="file_uploads")
    submissions: Mapped[List["AssignmentSubmission"]] = relationship(
        "AssignmentSubmission",
        back_populates="file_upload"
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="file_upload"
    )


class Document(BaseModel):
    """
    SQLAlchemy Model representing processed documents ready for RAG and search operations.
    """
    __tablename__ = "documents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSON(), nullable=True)  # Key-value metadata
    
    file_upload_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("file_uploads.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    file_upload: Mapped[Optional[FileUpload]] = relationship(FileUpload, back_populates="documents")
    notes: Mapped[List["Notes"]] = relationship(
        "Notes",
        back_populates="document"
    )


class Notes(BaseModel):
    """
    SQLAlchemy Model representing study notes uploaded by students/teachers.
    """
    __tablename__ = "notes"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    document: Mapped[Optional[Document]] = relationship(Document, back_populates="notes")
    course: Mapped[Optional["Course"]] = relationship("Course", back_populates="notes")
    user: Mapped["User"] = relationship("User", back_populates="notes")
    summary: Mapped[Optional["Summary"]] = relationship(
        "Summary",
        back_populates="notes",
        cascade="all, delete-orphan",
        uselist=False
    )


class Summary(BaseModel):
    """
    SQLAlchemy Model representing AI-generated summaries of notes.
    """
    __tablename__ = "summaries"

    notes_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    summary_text: Mapped[str] = mapped_column(Text(), nullable=False)
    key_points: Mapped[Optional[list]] = mapped_column(JSON(), nullable=True)  # List of summary bullet points
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    notes: Mapped[Notes] = relationship(Notes, back_populates="summary")
