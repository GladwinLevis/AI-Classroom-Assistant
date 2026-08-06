from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RechartsSeriesData(BaseModel):
    name: str
    value: float
    extra: Optional[Dict[str, Any]] = None


class NotificationBase(BaseModel):
    title: str
    content: str
    priority: str = "medium"
    category: str = "general"
    notification_type: str = "system"
    link: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: UUID


class NotificationResponse(NotificationBase):
    id: UUID
    user_id: UUID
    is_read: bool
    is_archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    target_type: str = "course"  # course, classroom, department, global
    course_id: Optional[UUID] = None
    classroom_id: Optional[UUID] = None
    department: Optional[str] = None


class AnnouncementResponse(BaseModel):
    id: UUID
    title: str
    content: str
    target_type: str
    creator_id: UUID
    course_id: Optional[UUID] = None
    classroom_id: Optional[UUID] = None
    department: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StudentDashboardResponse(BaseModel):
    student_id: UUID
    attendance_percentage: float
    attendance_trend: List[RechartsSeriesData] = []
    upcoming_classes: List[Dict[str, Any]] = []
    todays_schedule: List[Dict[str, Any]] = []
    upcoming_assignments: List[Dict[str, Any]] = []
    quiz_history: List[Dict[str, Any]] = []
    average_quiz_score: float
    recent_ai_summaries: List[Dict[str, Any]] = []
    recent_chatbot_sessions: List[Dict[str, Any]] = []
    study_progress: float
    weak_subjects: List[str] = []
    strong_subjects: List[str] = []
    recommended_topics: List[str] = []
    recommended_quizzes: List[Dict[str, Any]] = []
    learning_streak_days: int
    achievements: List[str] = []
    unread_notifications_count: int
    activity_timeline: List[Dict[str, Any]] = []


class TeacherDashboardResponse(BaseModel):
    teacher_id: UUID
    todays_classes: List[Dict[str, Any]] = []
    student_attendance_percentage: float
    attendance_trends: List[RechartsSeriesData] = []
    assignment_statistics: Dict[str, Any] = {}
    pending_assignment_reviews_count: int
    quiz_statistics: Dict[str, Any] = {}
    weak_topics_across_class: List[str] = []
    top_performing_students: List[Dict[str, Any]] = []
    low_performing_students: List[Dict[str, Any]] = []
    recent_ai_activity: List[Dict[str, Any]] = []
    recent_student_activity: List[Dict[str, Any]] = []
    announcements: List[AnnouncementResponse] = []
    unread_notifications_count: int


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_students: int
    total_teachers: int
    total_courses: int
    total_subjects: int
    attendance_overview_percentage: float
    system_health_status: str
    storage_usage_mb: float
    ai_requests_total: int
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    recent_logins: List[Dict[str, Any]] = []
    failed_login_attempts_count: int
    api_usage_stats: List[RechartsSeriesData] = []
    error_statistics: Dict[str, int] = {}
    celery_queue_status: str


class ReportGenerateRequest(BaseModel):
    report_type: str  # student, teacher, attendance, assignment, quiz, ai_usage, course, department
    format: str  # pdf, excel, csv
    filters: Optional[Dict[str, Any]] = None


class GeneratedReportResponse(BaseModel):
    id: UUID
    report_name: str
    report_type: str
    format: str
    file_path: str
    file_size: int
    generated_by_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class GlobalSearchResponse(BaseModel):
    students: List[Dict[str, Any]] = []
    teachers: List[Dict[str, Any]] = []
    assignments: List[Dict[str, Any]] = []
    quizzes: List[Dict[str, Any]] = []
    documents: List[Dict[str, Any]] = []
    courses: List[Dict[str, Any]] = []
    announcements: List[Dict[str, Any]] = []


class TimelineEventResponse(BaseModel):
    id: UUID
    user_id: UUID
    action: str
    entity_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
