import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, time, datetime, timezone, timedelta
from uuid import UUID

from app.core.security import create_access_token, get_password_hash
from app.models.security import Role
from app.models.user import User, UserRole, StudentProfile, TeacherProfile
from app.models.course import Subject, Course, Enrollment, Classroom
from app.models.attendance import AttendanceSession, AttendanceRecord, AttendanceSessionStatus, AttendanceStatus, AttendanceMode
from app.services.attendance import QRCodeService
from app.core.config import settings


@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    """
    Seeds essential lookup data including subjects, courses, teacher, students, and enrollments.
    """
    # 1. Create Roles if not existing
    roles = {}
    for role_enum in [UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN]:
        stmt = select(Role).filter(Role.name == role_enum.value)
        res = await db_session.execute(stmt)
        role = res.scalars().first()
        if not role:
            role = Role(name=role_enum.value, description=f"{role_enum.value} role")
            db_session.add(role)
        roles[role_enum.value] = role
    await db_session.flush()

    # 2. Create Teacher User & Profile
    teacher_user = User(
        email="teacher@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Jane",
        last_name="Smith",
        is_active=True,
        is_verified=True,
        roles=[roles[UserRole.TEACHER.value]]
    )
    db_session.add(teacher_user)
    await db_session.flush()

    teacher_profile = TeacherProfile(
        user_id=teacher_user.id,
        employee_id="EMP-9988",
        department="Computer Science"
    )
    db_session.add(teacher_profile)
    await db_session.flush()

    # 3. Create Student User & Profile
    student_user = User(
        email="student@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Bob",
        last_name="Johnson",
        is_active=True,
        is_verified=True,
        roles=[roles[UserRole.STUDENT.value]]
    )
    db_session.add(student_user)
    await db_session.flush()

    student_profile = StudentProfile(
        user_id=student_user.id,
        roll_number="CS-2026-001",
        academic_year="2026"
    )
    db_session.add(student_profile)
    await db_session.flush()

    # 4. Create Subject & Course & Classroom
    subject = Subject(
        name="Introduction to Python",
        code="CS-101",
        department="Computer Science"
    )
    db_session.add(subject)
    await db_session.flush()

    course = Course(
        name="Python Programming 101",
        code="CS-101-A",
        subject_id=subject.id,
        teacher_id=teacher_profile.id
    )
    db_session.add(course)
    await db_session.flush()

    classroom = Classroom(
        name="Lab Alpha",
        room_number="Room 101",
        capacity=30,
        course_id=course.id
    )
    db_session.add(classroom)
    await db_session.flush()

    # 5. Enroll student in course
    enrollment = Enrollment(
        student_id=student_profile.id,
        course_id=course.id,
        status="active"
    )
    db_session.add(enrollment)
    await db_session.flush()

    return {
        "teacher_user": teacher_user,
        "teacher_profile": teacher_profile,
        "student_user": student_user,
        "student_profile": student_profile,
        "course": course,
        "classroom": classroom,
        "subject": subject
    }


def get_auth_headers(user_id: UUID, role: str) -> dict:
    """Helper to generate JWT headers."""
    token = create_access_token(data={"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_session_lifecycle(client: AsyncClient, seed_data: dict, db_session: AsyncSession):
    """
    Tests session scheduling, activation, updating, listing and closure.
    """
    teacher = seed_data["teacher_user"]
    course = seed_data["course"]
    classroom = seed_data["classroom"]

    headers = get_auth_headers(teacher.id, UserRole.TEACHER.value)

    # 1. Create Session
    session_data = {
        "course_id": str(course.id),
        "classroom_id": str(classroom.id),
        "date": "2026-07-18",
        "start_time": "09:00:00",
        "end_time": "10:30:00",
        "attendance_mode": "manual"
    }

    response = await client.post("/api/v1/attendance/sessions", json=session_data, headers=headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["status"] == "scheduled"
    assert res_data["attendance_mode"] == "manual"
    session_id = res_data["id"]

    # 2. Activate Session
    update_data = {
        "status": "active"
    }
    response = await client.put(f"/api/v1/attendance/sessions/{session_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "active"

    # 3. List active sessions for Student
    student = seed_data["student_user"]
    stu_headers = get_auth_headers(student.id, UserRole.STUDENT.value)
    
    response = await client.get("/api/v1/attendance/sessions/active", headers=stu_headers)
    assert response.status_code == 200
    active_sessions = response.json()
    assert len(active_sessions) == 1
    assert active_sessions[0]["id"] == session_id

    # 4. Close Session
    response = await client.post(f"/api/v1/attendance/sessions/{session_id}/close", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_student_self_marking_manual(client: AsyncClient, seed_data: dict, db_session: AsyncSession):
    """
    Tests student self-attendance marking on a manual session.
    """
    teacher = seed_data["teacher_user"]
    student = seed_data["student_user"]
    course = seed_data["course"]

    # 1. Create and Activate manual session
    t_headers = get_auth_headers(teacher.id, UserRole.TEACHER.value)
    session_res = await client.post(
        "/api/v1/attendance/sessions", 
        json={
            "course_id": str(course.id),
            "date": str(date.today()),
            "attendance_mode": "manual"
        },
        headers=t_headers
    )
    session_id = session_res.json()["id"]
    await client.put(f"/api/v1/attendance/sessions/{session_id}", json={"status": "active"}, headers=t_headers)

    # 2. Mark attendance by student
    s_headers = get_auth_headers(student.id, UserRole.STUDENT.value)
    response = await client.post(f"/api/v1/attendance/mark/student?session_id={session_id}", headers=s_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "present"

    # 3. Try duplicate marking (should trigger 409 Conflict)
    response = await client.post(f"/api/v1/attendance/mark/student?session_id={session_id}", headers=s_headers)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_student_self_marking_qr_code(client: AsyncClient, seed_data: dict, db_session: AsyncSession):
    """
    Tests student QR scanner verification, signature checks, and expiration.
    """
    teacher = seed_data["teacher_user"]
    student = seed_data["student_user"]
    course = seed_data["course"]

    t_headers = get_auth_headers(teacher.id, UserRole.TEACHER.value)
    s_headers = get_auth_headers(student.id, UserRole.STUDENT.value)

    # 1. Create QR code session
    session_res = await client.post(
        "/api/v1/attendance/sessions", 
        json={
            "course_id": str(course.id),
            "date": str(date.today()),
            "attendance_mode": "qr_code"
        },
        headers=t_headers
    )
    session_id = session_res.json()["id"]
    await client.put(f"/api/v1/attendance/sessions/{session_id}", json={"status": "active"}, headers=t_headers)

    # 2. Try marking without QR token (should fail 422/400)
    response = await client.post(f"/api/v1/attendance/mark/student?session_id={session_id}", headers=s_headers)
    assert response.status_code == 422

    # 3. Generate QR token
    qr_res = await client.post(f"/api/v1/attendance/sessions/{session_id}/qr", headers=t_headers)
    assert qr_res.status_code == 200
    qr_token = qr_res.json()["qr_token"]

    # 4. Mark with valid QR token
    response = await client.post(
        f"/api/v1/attendance/mark/student?session_id={session_id}", 
        json={"qr_token": qr_token}, 
        headers=s_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "present"

    # 5. Verify expired QR token signature failure
    qr_service = QRCodeService(settings.JWT_SECRET_KEY)
    # Generate token that is already expired (e.g. -10s TTL)
    expired_token = qr_service.generate_qr_token(session_id, ttl_seconds=-10)

    # Create new session to test expired token verification
    session_res_2 = await client.post(
        "/api/v1/attendance/sessions", 
        json={
            "course_id": str(course.id),
            "date": str(date.today()),
            "attendance_mode": "qr_code"
        },
        headers=t_headers
    )
    session_id_2 = session_res_2.json()["id"]
    await client.put(f"/api/v1/attendance/sessions/{session_id_2}", json={"status": "active"}, headers=t_headers)

    response = await client.post(
        f"/api/v1/attendance/mark/student?session_id={session_id_2}", 
        json={"qr_token": expired_token}, 
        headers=s_headers
    )
    assert response.status_code == 422
    assert "expired" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_teacher_bulk_marking_and_reports(client: AsyncClient, seed_data: dict, db_session: AsyncSession):
    """
    Tests teacher bulk marking operations, record updates, analytics queries, and report generation.
    """
    teacher = seed_data["teacher_user"]
    student_profile = seed_data["student_profile"]
    course = seed_data["course"]

    t_headers = get_auth_headers(teacher.id, UserRole.TEACHER.value)

    # 1. Create and Activate manual session
    session_res = await client.post(
        "/api/v1/attendance/sessions", 
        json={
            "course_id": str(course.id),
            "date": str(date.today()),
            "attendance_mode": "manual"
        },
        headers=t_headers
    )
    session_id = session_res.json()["id"]
    await client.put(f"/api/v1/attendance/sessions/{session_id}", json={"status": "active"}, headers=t_headers)

    # 2. Bulk mark student late
    bulk_data = {
        "student_ids": [str(student_profile.id)],
        "status": "late"
    }
    response = await client.post(
        f"/api/v1/attendance/mark/teacher/bulk?session_id={session_id}", 
        json=bulk_data, 
        headers=t_headers
    )
    assert response.status_code == 200
    assert response.json()[0]["status"] == "late"

    # 3. Update single student status to excused
    update_res = await client.put(
        f"/api/v1/attendance/mark/session/{session_id}/student/{student_profile.id}",
        json={"status": "excused"},
        headers=t_headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "excused"

    # 4. Fetch course analytics
    analytics_res = await client.get(f"/api/v1/attendance/analytics/course/{course.id}", headers=t_headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["overall"]["excused_count"] == 1

    # 5. Fetch report preview
    report_res = await client.get(f"/api/v1/attendance/reports/course/{course.id}", headers=t_headers)
    assert report_res.status_code == 200
    assert len(report_res.json()["records"]) == 1

    # 6. Export report to CSV file download
    export_res = await client.get(f"/api/v1/attendance/reports/course/{course.id}/export", headers=t_headers)
    assert export_res.status_code == 200
    assert "Roll Number" in export_res.text
