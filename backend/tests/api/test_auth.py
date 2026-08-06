import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.security import Role
from app.models.user import User, UserRole
from app.core.redis import redis_manager


@pytest.mark.asyncio
async def test_student_registration_and_login_flow(client: AsyncClient, db_session: AsyncSession):
    """
    Tests complete student registration, email verification, and login flow.
    """
    # 1. Register student
    reg_data = {
        "email": "student@example.com",
        "password": "Password123!",
        "first_name": "John",
        "last_name": "Doe",
        "academic_year": "2026",
        "date_of_birth": "2008-01-01"
    }
    
    response = await client.post("/api/v1/auth/register/student", json=reg_data)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["email"] == reg_data["email"]
    assert res_data["is_verified"] is False

    # Try login before verification: should fail
    login_data = {
        "email": "student@example.com",
        "password": "Password123!"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "verify your email" in response.json()["error"]["message"]

    # 2. Get OTP code from memory (simulated Redis fallback database)
    otp_code = await redis_manager.get_otp("student@example.com")
    assert otp_code is not None

    # Verify email
    verify_data = {
        "email": "student@example.com",
        "otp": otp_code
    }
    response = await client.post("/api/v1/auth/verify-email", json=verify_data)
    assert response.status_code == 200
    assert response.json()["is_verified"] is True

    # 3. Login now: should succeed
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    login_res = response.json()
    assert "access_token" in login_res
    assert "refresh_token" in login_res
    assert login_res["user"]["email"] == "student@example.com"
    assert "student" in login_res["user"]["roles"]


@pytest.mark.asyncio
async def test_teacher_registration(client: AsyncClient, db_session: AsyncSession):
    """
    Tests teacher registration flow.
    """
    reg_data = {
        "email": "teacher@example.com",
        "password": "TeacherPassword123!",
        "first_name": "Jane",
        "last_name": "Smith",
        "employee_id": "T1001",
        "specialization": "Mathematics",
        "department": "Science"
    }
    response = await client.post("/api/v1/auth/register/teacher", json=reg_data)
    assert response.status_code == 201
    assert response.json()["email"] == reg_data["email"]


@pytest.mark.asyncio
async def test_admin_registration_restricted(client: AsyncClient, db_session: AsyncSession):
    """
    Tests that Admin registration is restricted to existing Admin roles.
    """
    reg_data = {
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "first_name": "Super",
        "last_name": "User",
        "access_level": "superadmin"
    }
    # Unauthenticated register admin call: should fail
    response = await client.post("/api/v1/auth/register/admin", json=reg_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_failed_logins_brute_force_lockout(client: AsyncClient, db_session: AsyncSession):
    """
    Tests brute-force lockouts after 5 consecutive login failures.
    """
    # Create verified student first
    student = User(
        email="failed_login@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Failed",
        last_name="User",
        is_active=True,
        is_verified=True
    )
    db_session.add(student)
    await db_session.flush()

    login_data = {
        "email": "failed_login@example.com",
        "password": "WrongPassword"
    }

    # First 4 attempts fail
    for i in range(1, 5):
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert f"Attempt {i} of 5" in response.json()["error"]["message"]

    # 5th attempt locks account
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "locked due to 5 consecutive login failures" in response.json()["error"]["message"]

    # Any subsequent attempt is locked
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "locked due to too many failed login attempts" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_password_strength_validation(client: AsyncClient):
    """
    Tests that weak passwords are rejected during registration.
    """
    reg_data = {
        "email": "weak@example.com",
        "password": "123",  # Too short, no upper/lower/number/special
        "first_name": "Weak",
        "last_name": "Password",
        "academic_year": "2026"
    }
    response = await client.post("/api/v1/auth/register/student", json=reg_data)
    assert response.status_code == 422
    assert "at least 8 characters" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_forgot_password_reset_flow(client: AsyncClient, db_session: AsyncSession):
    """
    Tests generating forgot password OTP, verifying OTP, and resetting password.
    """
    # Create student
    student = User(
        email="reset@example.com",
        hashed_password=get_password_hash("OldPassword123!"),
        first_name="Reset",
        last_name="User",
        is_active=True,
        is_verified=True
    )
    db_session.add(student)
    await db_session.flush()

    # 1. Trigger forgot password
    forgot_data = {"email": "reset@example.com"}
    response = await client.post("/api/v1/auth/forgot-password", json=forgot_data)
    assert response.status_code == 200

    # Retrieve OTP code
    otp = await redis_manager.get_otp("reset@example.com")
    assert otp is not None

    # 2. Verify OTP
    verify_data = {
        "email": "reset@example.com",
        "otp": otp
    }
    response = await client.post("/api/v1/auth/verify-otp", json=verify_data)
    assert response.status_code == 200

    # 3. Reset password
    reset_data = {
        "email": "reset@example.com",
        "otp": otp,
        "new_password": "NewSecurePassword123!"
    }
    response = await client.post("/api/v1/auth/reset-password", json=reset_data)
    assert response.status_code == 200

    # Try logging in with new password
    login_data = {
        "email": "reset@example.com",
        "password": "NewSecurePassword123!"
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
