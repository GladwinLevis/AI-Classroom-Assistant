from fastapi import APIRouter, Depends, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import (
    get_current_active_user, get_current_user, RoleChecker, 
    oauth2_scheme
)
from app.models.user import User, UserRole
from uuid import uuid4
from app.schemas.auth import (
    StudentRegisterRequest, TeacherRegisterRequest, AdminRegisterRequest,
    GenericRegisterRequest, LoginRequest, TokenResponse, UserProfileSchema, 
    ForgotPasswordRequest, VerifyOTPRequest, ResetPasswordRequest, 
    ResendVerificationRequest, VerifyEmailRequest
)
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=UserProfileSchema, status_code=status.HTTP_201_CREATED)
async def register_generic(
    request: GenericRegisterRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Unified generic registration endpoint handling both student and teacher signups.
    """
    auth_service = AuthService(db)
    if request.role == "teacher":
        t_req = TeacherRegisterRequest(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            employee_id=request.employee_id or f"EMP-{uuid4().hex[:6].upper()}",
            department=request.department or "General"
        )
        user = await auth_service.register_teacher(t_req)
    else:
        s_req = StudentRegisterRequest(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            academic_year=request.academic_year or "2026",
            roll_number=request.roll_number or f"STU-{uuid4().hex[:6].upper()}"
        )
        user = await auth_service.register_student(s_req)

    return UserProfileSchema(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        is_verified=user.is_verified
    )


@router.post("/register/student", response_model=UserProfileSchema, status_code=status.HTTP_201_CREATED)
async def register_student(
    request: StudentRegisterRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new student profile in the system.
    """
    auth_service = AuthService(db)
    user = await auth_service.register_student(request)
    return UserProfileSchema(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        is_verified=user.is_verified
    )


@router.post("/register/teacher", response_model=UserProfileSchema, status_code=status.HTTP_201_CREATED)
async def register_teacher(
    request: TeacherRegisterRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new teacher profile in the system.
    """
    auth_service = AuthService(db)
    user = await auth_service.register_teacher(request)
    return UserProfileSchema(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        is_verified=user.is_verified
    )


@router.post(
    "/register/admin", 
    response_model=UserProfileSchema, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RoleChecker([UserRole.ADMIN]))]
)
async def register_admin(
    request: AdminRegisterRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new admin profile. Restricted: Can only be called by an existing Admin.
    """
    auth_service = AuthService(db)
    user = await auth_service.register_admin(request)
    return UserProfileSchema(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        is_verified=user.is_verified
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates user. Returns access/refresh tokens and basic profile.
    Locks account for 15 minutes after 5 failed attempts.
    """
    auth_service = AuthService(db)
    return await auth_service.authenticate_user(login_data)

# Custom request model just for logout
from pydantic import BaseModel

class UserLogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    logout_data: UserLogoutRequest,
    authorization: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Logs out the user. Blacklists access token in Redis and revokes refresh token.
    """
    auth_service = AuthService(db)
    await auth_service.logout_user(authorization, logout_data.refresh_token)
    return {"success": True, "message": "Logged out successfully."}


class TokenRefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Secure Refresh Token Rotation. Returns new Access and Refresh tokens.
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(refresh_data.refresh_token)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    forgot_req: ForgotPasswordRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Generates a secure 6-digit password reset OTP and stores it in Redis.
    Logs the OTP to stdout/logs for development.
    """
    auth_service = AuthService(db)
    await auth_service.send_forgot_password_otp(forgot_req.email)
    return {
        "success": True, 
        "message": "If the account exists, a 6-digit verification code has been dispatched."
    }


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(
    verify_req: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies if the submitted password-reset OTP matches the stored Redis code.
    """
    auth_service = AuthService(db)
    await auth_service.verify_otp_code(verify_req.email, verify_req.otp)
    return {"success": True, "message": "Verification code is valid."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_req: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resets user password to new_password if OTP matches.
    """
    auth_service = AuthService(db)
    await auth_service.reset_password_with_otp(
        reset_req.email, reset_req.otp, reset_req.new_password
    )
    return {"success": True, "message": "Password has been reset successfully."}


@router.post("/send-verification", status_code=status.HTTP_200_OK)
async def send_verification(
    resend_req: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generates and sends a new email verification code OTP.
    """
    auth_service = AuthService(db)
    await auth_service.send_email_verification_otp(resend_req.email)
    return {"success": True, "message": "Verification code has been dispatched."}


@router.post("/verify-email", response_model=UserProfileSchema, status_code=status.HTTP_200_OK)
async def verify_email(
    verify_req: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies user email address. Unlocks login access.
    """
    auth_service = AuthService(db)
    user = await auth_service.verify_email_with_otp(verify_req.email, verify_req.otp)
    return UserProfileSchema(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        roles=[r.name for r in user.roles],
        is_active=user.is_active,
        is_verified=user.is_verified
    )


@router.get("/me", response_model=UserProfileSchema)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves the currently authenticated user's profile and active roles.
    """
    role_names = [r.name for r in current_user.roles]
    return UserProfileSchema(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        roles=role_names,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified
    )
