# Schemas package containing Pydantic data validation models
from app.schemas.auth import (
    LoginRequest, TokenResponse, TokenPayload, StudentRegisterRequest, 
    TeacherRegisterRequest, AdminRegisterRequest, ForgotPasswordRequest, 
    VerifyOTPRequest, ResetPasswordRequest, VerifyEmailRequest
)
from app.schemas.user import UserResponse, UserUpdate, UserCreate
from app.schemas.attendance import AttendanceResponse, AttendanceCreate, AttendanceUpdate
from app.schemas.note import NoteResponse, NoteCreate, NoteUpdate
from app.schemas.quiz import QuizResponse, QuizCreate, QuestionResponse, QuestionCreate
from app.schemas.assignment import (
    AssignmentResponse, AssignmentCreate, AssignmentSubmissionResponse, AssignmentSubmissionCreate
)
