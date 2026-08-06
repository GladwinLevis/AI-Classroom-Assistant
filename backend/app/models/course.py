import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Integer, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Subject(BaseModel):
    """
    SQLAlchemy Model representing academic subjects (e.g. Mathematics, History).
    """
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="subject",
        cascade="all, delete-orphan"
    )


class Course(BaseModel):
    """
    SQLAlchemy Model representing a specific running instance of a subject.
    """
    __tablename__ = "courses"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teacher_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    subject: Mapped[Subject] = relationship(Subject, back_populates="courses")
    teacher: Mapped["TeacherProfile"] = relationship("TeacherProfile", back_populates="courses")
    classrooms: Mapped[List["Classroom"]] = relationship(
        "Classroom",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    attendance_sessions: Mapped[List["AttendanceSession"]] = relationship(
        "AttendanceSession",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    quizzes: Mapped[List["Quiz"]] = relationship(
        "Quiz",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    notes: Mapped[List["Notes"]] = relationship(
        "Notes",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    announcements: Mapped[List["Announcement"]] = relationship(
        "Announcement",
        back_populates="course",
        cascade="all, delete-orphan"
    )


class Classroom(BaseModel):
    """
    SQLAlchemy Model representing physical or virtual spaces allocated to courses.
    """
    __tablename__ = "classrooms"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    room_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Relationships
    course: Mapped[Optional[Course]] = relationship(Course, back_populates="classrooms")


class Enrollment(BaseModel):
    """
    SQLAlchemy Model mapping student enrollment in courses.
    """
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_enrollment"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, completed, dropped

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="enrollments")
    course: Mapped[Course] = relationship(Course, back_populates="enrollments")
