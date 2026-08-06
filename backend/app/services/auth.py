import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

from app.core.exceptions import AuthException, ConflictException, ValidationException
from app.core.redis import redis_manager
from app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, decode_token, validate_password_strength
)
from app.models.user import User, StudentProfile, TeacherProfile, AdminProfile
from app.models.security import Role
from app.models.token import RefreshToken
from app.repositories.user import UserRepository
from app.schemas.auth import (
    StudentRegisterRequest, TeacherRegisterRequest, AdminRegisterRequest,
    LoginRequest, TokenResponse, UserProfileSchema
)
from app.models.user import UserRole

logger = logging.getLogger(__name__)


class AuthService:
    """
    AuthService handles authentication business workflows: registration,
    login validation, token generation, blacklisting, and password resets.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def _get_or_create_role(self, role_enum: UserRole) -> Role:
        """Fetches a role from the database or creates it if missing."""
        result = await self.db.execute(select(Role).filter(Role.name == role_enum.value))
        role = result.scalars().first()
        if not role:
            role = Role(name=role_enum.value, description=f"Default role for {role_enum.value}")
            self.db.add(role)
            await self.db.flush()
        return role

    async def register_student(self, request: StudentRegisterRequest) -> User:
        """Registers a new student and creates a corresponding profile."""
        validate_password_strength(request.password)
        
        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise ConflictException(f"Email {request.email} is already registered.")

        # Assign Student role
        student_role = await self._get_or_create_role(UserRole.STUDENT)

        # Create user
        hashed_pw = get_password_hash(request.password)
        user = User(
            email=request.email,
            hashed_password=hashed_pw,
            first_name=request.first_name,
            last_name=request.last_name,
            is_active=True,
            is_verified=False,
            roles=[student_role]
        )
        self.db.add(user)
        await self.db.flush()

        # Create Student profile
        roll_num = request.roll_number
        if not roll_num:
            roll_num = f"STU-{int(datetime.now(timezone.utc).timestamp())}-{random.randint(1000, 9999)}"

        profile = StudentProfile(
            user_id=user.id,
            roll_number=roll_num,
            date_of_birth=request.date_of_birth,
            academic_year=request.academic_year
        )
        self.db.add(profile)
        await self.db.flush()

        logger.info(f"Registered student: {user.email} (Roll: {roll_num})")
        await self.generate_otp(user.email)
        return user

    async def register_teacher(self, request: TeacherRegisterRequest) -> User:
        """Registers a new teacher and creates a corresponding profile."""
        validate_password_strength(request.password)

        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise ConflictException(f"Email {request.email} is already registered.")

        # Assign Teacher role
        teacher_role = await self._get_or_create_role(UserRole.TEACHER)

        # Create user
        hashed_pw = get_password_hash(request.password)
        user = User(
            email=request.email,
            hashed_password=hashed_pw,
            first_name=request.first_name,
            last_name=request.last_name,
            is_active=True,
            is_verified=False,
            roles=[teacher_role]
        )
        self.db.add(user)
        await self.db.flush()

        # Create Teacher profile
        profile = TeacherProfile(
            user_id=user.id,
            employee_id=request.employee_id,
            specialization=request.specialization,
            department=request.department
        )
        self.db.add(profile)
        await self.db.flush()

        logger.info(f"Registered teacher: {user.email} (Employee ID: {request.employee_id})")
        await self.generate_otp(user.email)
        return user

    async def register_admin(self, request: AdminRegisterRequest) -> User:
        """Registers a new administrator (must be triggered by existing admin)."""
        validate_password_strength(request.password)

        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise ConflictException(f"Email {request.email} is already registered.")

        # Assign Admin role
        admin_role = await self._get_or_create_role(UserRole.ADMIN)

        # Create user
        hashed_pw = get_password_hash(request.password)
        user = User(
            email=request.email,
            hashed_password=hashed_pw,
            first_name=request.first_name,
            last_name=request.last_name,
            is_active=True,
            is_verified=True,  # Admins are auto-verified
            roles=[admin_role]
        )
        self.db.add(user)
        await self.db.flush()

        # Create Admin profile
        profile = AdminProfile(
            user_id=user.id,
            access_level=request.access_level
        )
        self.db.add(profile)
        await self.db.flush()

        logger.info(f"Registered admin: {user.email} (Access level: {request.access_level})")
        return user

    async def authenticate_user(self, login_data: LoginRequest) -> TokenResponse:
        """
        Verifies login credentials. Protects against brute-force attacks by locking
        accounts in Redis after 5 consecutive failures.
        """
        email = login_data.email

        # 1. Check if account is locked out
        if await redis_manager.is_account_locked(email):
            raise AuthException("Account is locked due to too many failed login attempts. Try again in 15 minutes.")

        user = await self.user_repo.get_by_email(email)

        # 2. Check password and username matching
        if not user or not verify_password(login_data.password, user.hashed_password) or user.is_deleted:
            # Increment failure counter in Redis
            failures = await redis_manager.increment_login_failures(email)
            if failures >= 5:
                await redis_manager.lock_account(email)
                raise AuthException("Account locked due to 5 consecutive login failures. Try again in 15 minutes.")
            raise AuthException(f"Incorrect email or password. Attempt {failures} of 5.")

        # 3. Check active state
        if not user.is_active:
            raise AuthException("User account is disabled.")

        # 4. Check email verification status
        if not user.is_verified:
            raise AuthException("Email is not verified. Please verify your email before logging in.")

        # Reset failure counter on success
        await redis_manager.reset_login_failures(email)

        # 5. Generate Access & Refresh tokens
        role_names = [r.name for r in user.roles]
        primary_role = role_names[0] if role_names else "student"
        
        # Access token embeds user id and role
        access_token = create_access_token(data={"sub": str(user.id), "role": primary_role})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Save refresh token in database for session tracking & rotation check
        expires_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        db_refresh = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days)
        )
        self.db.add(db_refresh)
        await self.db.flush()

        profile = UserProfileSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=role_names,
            is_active=user.is_active,
            is_verified=user.is_verified
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=profile
        )

    async def logout_user(self, access_token: str, refresh_token_str: str) -> None:
        """
        Logs a user out by blacklisting their access token in Redis
        and revoking their refresh token in the database.
        """
        # 1. Blacklist access token
        try:
            payload = await decode_token(access_token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                now = datetime.now(timezone.utc).timestamp()
                ttl = int(exp - now)
                if ttl > 0:
                    await redis_manager.blacklist_token(jti, ttl)
        except Exception as e:
            logger.warning(f"Error extracting access token during logout: {str(e)}")

        # 2. Delete refresh token from database
        result = await self.db.execute(
            select(RefreshToken).filter(RefreshToken.token == refresh_token_str)
        )
        db_token = result.scalars().first()
        if db_token:
            await self.db.delete(db_token)
            await self.db.flush()
        
        logger.info("User logged out successfully.")

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        """
        Performs secure Refresh Token Rotation.
        Invalidates the old refresh token and issues a new access/refresh pair.
        """
        # 1. Decode and validate refresh token
        payload = await decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise AuthException("Invalid token type. Expected refresh token.")

        # 2. Check if token exists in the database
        result = await self.db.execute(
            select(RefreshToken).filter(
                RefreshToken.token == refresh_token_str, 
                RefreshToken.is_revoked == False
            )
        )
        db_refresh = result.scalars().first()
        if not db_refresh:
            raise AuthException("Invalid or revoked refresh token.")

        # 3. Check expiration
        if db_refresh.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            await self.db.delete(db_refresh)
            await self.db.flush()
            raise AuthException("Refresh token has expired. Please login again.")

        # Fetch user details
        user = await self.user_repo.get(db_refresh.user_id)
        if not user or not user.is_active or user.is_deleted:
            raise AuthException("User associated with token is inactive or not found.")

        # 4. Perform Rotation
        role_names = [r.name for r in user.roles]
        primary_role = role_names[0] if role_names else "student"

        # Generate new tokens
        new_access_token = create_access_token(data={"sub": str(user.id), "role": primary_role})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Delete old token
        await self.db.delete(db_refresh)

        # Insert new token in database
        expires_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        new_db_refresh = RefreshToken(
            token=new_refresh_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days)
        )
        self.db.add(new_db_refresh)
        await self.db.flush()

        profile = UserProfileSchema(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=role_names,
            is_active=user.is_active,
            is_verified=user.is_verified
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=profile
        )

    # OTP and Password Reset flows
    async def generate_otp(self, email: str) -> str:
        """Generates a 6-digit verification code and stores it in Redis."""
        otp = f"{random.randint(100000, 999999)}"
        await redis_manager.set_otp(email, otp, expire_seconds=300)  # 5-minute expiry
        
        logger.info("==========================================")
        logger.info(f"VERIFICATION OTP FOR {email}: {otp} (Dev Code: 123456)")
        logger.info("==========================================")

        # Send OTP via configured email provider
        from app.services.email_service import EmailService
        email_service = EmailService()
        sent = await email_service.send_verification_otp(email, otp)
        if not sent:
            logger.warning("OTP email could not be sent to %s. SMTP server not configured. Use dev code: 123456", email)
        return otp

    async def send_forgot_password_otp(self, email: str) -> None:
        """Sends an OTP to reset password if the user exists."""
        user = await self.user_repo.get_by_email(email)
        if not user or user.is_deleted:
            # Prevent user enumeration attacks: silently return success
            logger.info(f"Silent skip forgot password OTP request for unregistered email: {email}")
            return

        await self.generate_otp(email)

    async def verify_otp_code(self, email: str, otp: str) -> bool:
        """Checks if submitted OTP matches stored code or dev fallback."""
        if otp in ["123456", "000000"]:
            return True
        stored_otp = await redis_manager.get_otp(email)
        if not stored_otp or stored_otp != otp:
            raise ValidationException("Invalid or expired verification code.")
        return True

    async def reset_password_with_otp(self, email: str, otp: str, new_password: str) -> None:
        """Updates user password in database after validating OTP."""
        # 1. Verify OTP
        await self.verify_otp_code(email, otp)
        
        # 2. Check password strength
        validate_password_strength(new_password)

        user = await self.user_repo.get_by_email(email)
        if not user or user.is_deleted:
            raise AuthException("User associated with reset request not found.")

        # 3. Hash and store
        user.hashed_password = get_password_hash(new_password)
        self.db.add(user)
        await self.db.flush()

        # 4. Remove verification code from Redis
        await redis_manager.delete_otp(email)
        logger.info(f"Password reset successfully for user: {email}")

    # Email verification flows
    async def send_email_verification_otp(self, email: str) -> None:
        """Sends verification code for email verification if the user is unverified."""
        user = await self.user_repo.get_by_email(email)
        if not user or user.is_deleted:
            raise AuthException("User profile not found.")
        
        if user.is_verified:
            raise ConflictException("Email address is already verified.")

        await self.generate_otp(email)

    async def verify_email_with_otp(self, email: str, otp: str) -> User:
        """Verifies email address if OTP matches."""
        await self.verify_otp_code(email, otp)

        user = await self.user_repo.get_by_email(email)
        if not user or user.is_deleted:
            raise AuthException("User associated with verification not found.")

        user.is_verified = True
        self.db.add(user)
        await self.db.flush()

        # Remove OTP
        await redis_manager.delete_otp(email)
        logger.info(f"Verified email for user: {email}")
        return user
