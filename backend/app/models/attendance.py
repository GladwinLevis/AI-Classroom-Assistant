import uuid
from datetime import date, time, datetime
from typing import List, Optional
import enum
from sqlalchemy import Date, Time, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


class AttendanceMode(str, enum.Enum):
    MANUAL = "manual"
    QR_CODE = "qr_code"
    FACE_RECOGNITION = "face_recognition"
    HYBRID = "hybrid"


class AttendanceSessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Attendance(BaseModel):
    """
    SQLAlchemy Model representing daily, school-wide general student attendance.
    """
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_daily_attendance"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus),
        default=AttendanceStatus.PRESENT,
        nullable=False
    )
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="attendances")


class AttendanceSession(BaseModel):
    """
    SQLAlchemy Model representing specific class or lecture slots for tracking session-based attendance.
    """
    __tablename__ = "attendance_sessions"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    classroom_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    start_time: Mapped[Optional[time]] = mapped_column(Time(), nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time(), nullable=True)
    
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teacher_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    attendance_mode: Mapped[AttendanceMode] = mapped_column(
        Enum(AttendanceMode),
        default=AttendanceMode.MANUAL,
        nullable=False
    )
    status: Mapped[AttendanceSessionStatus] = mapped_column(
        Enum(AttendanceSessionStatus),
        default=AttendanceSessionStatus.SCHEDULED,
        nullable=False
    )
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="attendance_sessions")
    classroom: Mapped[Optional["Classroom"]] = relationship("Classroom")
    records: Mapped[List["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class AttendanceRecord(BaseModel):
    """
    SQLAlchemy Model storing attendance statuses mapped to specific classroom slots/sessions.
    """
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_student_session_attendance"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus),
        default=AttendanceStatus.PRESENT,
        nullable=False
    )
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    marked_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    session: Mapped[AttendanceSession] = relationship(AttendanceSession, back_populates="records")
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="attendance_records")
