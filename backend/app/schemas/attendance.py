from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, time, datetime
from uuid import UUID
from app.models.attendance import AttendanceStatus, AttendanceMode, AttendanceSessionStatus


class AttendanceSessionCreate(BaseModel):
    """Schema representing requests to create a new attendance session."""
    course_id: UUID
    classroom_id: Optional[UUID] = None
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    attendance_mode: AttendanceMode = AttendanceMode.MANUAL


class AttendanceSessionUpdate(BaseModel):
    """Schema representing requests to update an attendance session."""
    classroom_id: Optional[UUID] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    attendance_mode: Optional[AttendanceMode] = None
    status: Optional[AttendanceSessionStatus] = None


class AttendanceSessionResponse(BaseModel):
    """Schema representing an attendance session response."""
    id: UUID
    course_id: UUID
    classroom_id: Optional[UUID] = None
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    teacher_id: UUID
    attendance_mode: AttendanceMode
    status: AttendanceSessionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttendanceRecordMark(BaseModel):
    """Schema representing a single attendance mark request by a student or teacher."""
    status: AttendanceStatus = AttendanceStatus.PRESENT


class AttendanceRecordResponse(BaseModel):
    """Schema representing attendance record details."""
    id: UUID
    session_id: Optional[UUID] = None
    student_id: UUID
    status: AttendanceStatus
    marked_at: datetime
    marked_by_id: Optional[UUID] = None
    student_name: Optional[str] = None
    course_name: Optional[str] = None
    remarks: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceBulkMarkRequest(BaseModel):
    """Schema representing teacher bulk marking attendance."""
    student_ids: List[UUID]
    status: AttendanceStatus


class QRGenerateResponse(BaseModel):
    """Schema representing generated QR Code security details."""
    qr_token: str
    session_id: UUID
    expires_at: datetime


class QRScanRequest(BaseModel):
    """Schema representing student scanner submission payload."""
    qr_token: str


class AttendanceStats(BaseModel):
    """Schema representing summary metrics for attendance reports or charts."""
    attendance_percentage: float
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    total_count: int


class SubjectWiseStats(BaseModel):
    """Schema representing summary metrics for a specific subject."""
    subject_id: UUID
    subject_name: str
    subject_code: str
    stats: AttendanceStats


class CourseWiseStats(BaseModel):
    """Schema representing summary metrics for a specific course."""
    course_id: UUID
    course_name: str
    course_code: str
    stats: AttendanceStats


class AttendanceDashboardAnalytics(BaseModel):
    """Schema representing a teacher/student attendance dashboard statistics package."""
    overall: AttendanceStats
    course_wise: List[CourseWiseStats] = []
    subject_wise: List[SubjectWiseStats] = []
    weekly_chart_data: Dict[str, AttendanceStats] = {}
    monthly_chart_data: Dict[str, AttendanceStats] = {}


class StudentAttendanceSummary(BaseModel):
    """Schema representing summary metrics for a student's personal view."""
    student_id: UUID
    stats: AttendanceStats
    course_wise: List[CourseWiseStats] = []


class StudentAttendanceReportRow(BaseModel):
    """Schema representing row detail of student attendance sheet."""
    student_id: UUID
    first_name: str
    last_name: str
    roll_number: str
    stats: AttendanceStats


class AttendanceReportResponse(BaseModel):
    """Schema representing an attendance report payload."""
    report_type: str  # student, class, subject, teacher, monthly, semester
    generated_at: datetime
    records: List[StudentAttendanceReportRow]


class AttendanceCreate(BaseModel):
    """Schema representing requests to log general daily attendance."""
    user_id: UUID
    date: date
    status: AttendanceStatus
    remarks: Optional[str] = None


class AttendanceUpdate(BaseModel):
    """Schema representing updates to general daily attendance."""
    status: Optional[AttendanceStatus] = None
    remarks: Optional[str] = None


class AttendanceResponse(BaseModel):
    """Schema representing general daily attendance details."""
    id: UUID
    user_id: UUID
    date: date
    status: AttendanceStatus
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
