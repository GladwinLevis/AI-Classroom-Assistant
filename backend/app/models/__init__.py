# Models package containing SQLAlchemy model definitions
from app.models.base import Base, BaseModel, TimestampMixin, SoftDeleteMixin
from app.models.security import Permission, Role, role_permissions, user_roles
from app.models.user import User, StudentProfile, TeacherProfile, AdminProfile
from app.models.token import RefreshToken, TokenBlacklist
from app.models.course import Subject, Course, Classroom, Enrollment
from app.models.attendance import AttendanceStatus, Attendance, AttendanceSession, AttendanceRecord
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentFeedback
from app.models.document import FileUpload, Document, Notes, Summary
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from app.models.communication import ChatSession, ChatMessage, Notification, Announcement
from app.models.analytics import ActivityLog, AuditLog, DashboardAnalytics
from app.models.reports import GeneratedReport
from app.models.gamification import UserGamification
from app.models.academic_calendar import CalendarEvent, SmartReminder
