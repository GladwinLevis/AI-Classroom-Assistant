from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date
from uuid import UUID


class UserProfileSchema(BaseModel):
    """
    Schema representing user profile details returned on login and current user checks.
    """
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    roles: List[str]
    is_active: bool
    is_verified: bool

    class Config:
        from_attributes = True


class GenericRegisterRequest(BaseModel):
    """Schema representing generic signup requests."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters.")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: Optional[str] = "student"
    academic_year: Optional[str] = "2026"
    roll_number: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = "General"


class StudentRegisterRequest(BaseModel):
    """Schema representing requests to register a student."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters.")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    academic_year: str = Field(..., min_length=1, max_length=20)
    roll_number: Optional[str] = None
    date_of_birth: Optional[date] = None


class TeacherRegisterRequest(BaseModel):
    """Schema representing requests to register a teacher."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters.")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    employee_id: str = Field(..., min_length=1, max_length=50)
    specialization: Optional[str] = None
    department: str = Field(..., min_length=1, max_length=100)


class AdminRegisterRequest(BaseModel):
    """Schema representing requests to register an administrator."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters.")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    access_level: str = Field("standard", min_length=1, max_length=50)


class LoginRequest(BaseModel):
    """Schema representing a user login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema representing an issued authentication token response with user profile."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Duration in seconds
    user: UserProfileSchema


class TokenPayload(BaseModel):
    """Schema representing token payload extracted from JWT validation."""
    sub: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None
    jti: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """Schema representing request to send OTP for forgotten password."""
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    """Schema representing verification of an OTP."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code.")


class ResetPasswordRequest(BaseModel):
    """Schema representing request to update password using a verified OTP."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code.")
    new_password: str = Field(..., min_length=8, description="New secure password.")


class ResendVerificationRequest(BaseModel):
    """Schema representing request to resend account verification email OTP."""
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    """Schema representing email verification using OTP."""
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code.")
