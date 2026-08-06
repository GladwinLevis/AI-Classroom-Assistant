import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import ForeignKey, String, Text, Float, DateTime, Boolean, JSON, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Assignment(BaseModel):
    """
    SQLAlchemy Model representing student assignments assigned under specific courses.
    """
    __tablename__ = "assignments"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    instructions: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    max_points: Mapped[float] = mapped_column(Float(), default=100.0, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rubric: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reference_material_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("file_uploads.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="assignments")
    submissions: Mapped[List["AssignmentSubmission"]] = relationship(
        "AssignmentSubmission",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )
    reference_material: Mapped[Optional["FileUpload"]] = relationship("FileUpload")


class AssignmentSubmission(BaseModel):
    """
    SQLAlchemy Model representing student work submissions.
    """
    __tablename__ = "assignment_submissions"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    file_upload_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("file_uploads.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    submitted_text: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="submitted")  # submitted, graded, late
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, processing, evaluated, failed

    # Relationships
    assignment: Mapped[Assignment] = relationship(Assignment, back_populates="submissions")
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="submissions")
    file_upload: Mapped[Optional["FileUpload"]] = relationship("FileUpload")
    feedback: Mapped[Optional["AssignmentFeedback"]] = relationship(
        "AssignmentFeedback",
        back_populates="submission",
        cascade="all, delete-orphan",
        uselist=False
    )


class AssignmentFeedback(BaseModel):
    """
    SQLAlchemy Model representing feedback (both teacher reviews and AI grading results).
    """
    __tablename__ = "assignment_feedback"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignment_submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    grader_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    feedback_text: Mapped[str] = mapped_column(Text(), nullable=False)
    grade_score: Mapped[float] = mapped_column(Float(), nullable=False)
    ai_score: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    final_score: Mapped[Optional[float]] = mapped_column(Float(), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending_teacher_review", nullable=False)
    plagiarism_score: Mapped[float] = mapped_column(Float(), default=0.0, nullable=False)
    rubric_evaluation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    strengths: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    grammar_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    similarity_report: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    submission: Mapped[AssignmentSubmission] = relationship(AssignmentSubmission, back_populates="feedback")
    grader: Mapped[Optional["User"]] = relationship("User")
