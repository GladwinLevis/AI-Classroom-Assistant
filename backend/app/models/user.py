import uuid
import enum
from datetime import date
from typing import List, Optional
from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from app.models.security import user_roles


class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"



class User(BaseModel):
    """
    SQLAlchemy Model representing the main system User credentials and profile.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users"
    )
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )
    teacher_profile: Mapped[Optional["TeacherProfile"]] = relationship(
        "TeacherProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )
    admin_profile: Mapped[Optional["AdminProfile"]] = relationship(
        "AdminProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notes: Mapped[List["Notes"]] = relationship(
        "Notes",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    announcements: Mapped[List["Announcement"]] = relationship(
        "Announcement",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    quizzes: Mapped[List["Quiz"]] = relationship(
        "Quiz",
        back_populates="creator"
    )
    file_uploads: Mapped[List["FileUpload"]] = relationship(
        "FileUpload",
        back_populates="uploader"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user"
    )


class StudentProfile(BaseModel):
    """
    SQLAlchemy Model representing student-specific metadata.
    """
    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    roll_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date(), nullable=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    user: Mapped[User] = relationship(User, back_populates="student_profile")
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    submissions: Mapped[List["AssignmentSubmission"]] = relationship(
        "AssignmentSubmission",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    quiz_attempts: Mapped[List["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="student",
        cascade="all, delete-orphan"
    )


class TeacherProfile(BaseModel):
    """
    SQLAlchemy Model representing teacher-specific metadata.
    """
    __tablename__ = "teacher_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    specialization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    user: Mapped[User] = relationship(User, back_populates="teacher_profile")
    courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="teacher",
        cascade="all, delete-orphan"
    )


class AdminProfile(BaseModel):
    """
    SQLAlchemy Model representing system administrator-specific metadata.
    """
    __tablename__ = "admin_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    access_level: Mapped[str] = mapped_column(String(50), default="standard", nullable=False)

    # Relationships
    user: Mapped[User] = relationship(User, back_populates="admin_profile")
