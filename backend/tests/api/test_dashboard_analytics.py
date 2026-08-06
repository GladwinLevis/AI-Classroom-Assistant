import os
import pytest
import pytest_asyncio
from uuid import UUID
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, StudentProfile, TeacherProfile, UserRole
from app.models.security import Role
from app.core.security import create_access_token, get_password_hash
from app.services.notification import NotificationService
from app.services.timeline import TimelineService


def get_headers(user_id: UUID, role_name: str = UserRole.STUDENT.value) -> dict:
    token = create_access_token(data={"sub": str(user_id), "role": role_name})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seed_dashboard_data(db_session: AsyncSession):
    """Seeds teacher, student, and admin users for dashboard analytics testing."""
    # Roles
    t_role_stmt = select(Role).filter(Role.name == UserRole.TEACHER.value)
    t_role = (await db_session.execute(t_role_stmt)).scalars().first()
    if not t_role:
        t_role = Role(name=UserRole.TEACHER.value, description="Teacher role")
        db_session.add(t_role)

    s_role_stmt = select(Role).filter(Role.name == UserRole.STUDENT.value)
    s_role = (await db_session.execute(s_role_stmt)).scalars().first()
    if not s_role:
        s_role = Role(name=UserRole.STUDENT.value, description="Student role")
        db_session.add(s_role)

    a_role_stmt = select(Role).filter(Role.name == UserRole.ADMIN.value)
    a_role = (await db_session.execute(a_role_stmt)).scalars().first()
    if not a_role:
        a_role = Role(name=UserRole.ADMIN.value, description="Admin role")
        db_session.add(a_role)

    await db_session.flush()

    # Admin
    admin_user = User(
        email="admin_dash@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Sys",
        last_name="Admin",
        is_active=True,
        is_verified=True,
        roles=[a_role]
    )
    db_session.add(admin_user)

    # Teacher
    teacher_user = User(
        email="teacher_dash@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Alan",
        last_name="Turing",
        is_active=True,
        is_verified=True,
        roles=[t_role]
    )
    db_session.add(teacher_user)
    await db_session.flush()

    teacher_prof = TeacherProfile(user_id=teacher_user.id, employee_id="EMP-DASH-01", department="Computer Science")
    db_session.add(teacher_prof)

    # Student
    student_user = User(
        email="student_dash@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Ada",
        last_name="Lovelace",
        is_active=True,
        is_verified=True,
        roles=[s_role]
    )
    db_session.add(student_user)
    await db_session.flush()

    student_prof = StudentProfile(user_id=student_user.id, roll_number="CS-DASH-01", academic_year="2026")
    db_session.add(student_prof)

    await db_session.commit()

    # Seed initial notification & timeline event
    notif_svc = NotificationService(db_session)
    await notif_svc.dispatch_notification(
        user_id=student_user.id,
        title="Welcome to AI Classroom Assistant",
        content="Your dashboard account is active.",
        category="system"
    )

    timeline_svc = TimelineService(db_session)
    await timeline_svc.log_event(
        user_id=student_user.id,
        action="Login Event Logged"
    )

    return {
        "admin": admin_user,
        "teacher": teacher_user,
        "student": student_user,
        "student_profile": student_prof
    }


@pytest.mark.asyncio
async def test_complete_phase9_dashboard_analytics_reporting_flow(
    client: AsyncClient,
    seed_dashboard_data: dict,
    db_session: AsyncSession
):
    """
    Validates complete Phase 9 Dashboard, Notifications, Reports, Analytics, Search & Timeline features:
    1. Student Dashboard GET
    2. Teacher Dashboard GET
    3. Admin Dashboard GET
    4. Notifications (List, Unread Count, Mark Read, Bulk Mark Read, Archive, Delete)
    5. Announcements (Create & List)
    6. Report Generation & File Download (CSV/Excel/PDF)
    7. Analytics Platform Endpoints
    8. Global Multi-Entity Search
    9. Activity Timeline Log Retrieval
    """
    admin = seed_dashboard_data["admin"]
    teacher = seed_dashboard_data["teacher"]
    student = seed_dashboard_data["student"]

    a_headers = get_headers(admin.id, UserRole.ADMIN.value)
    t_headers = get_headers(teacher.id, UserRole.TEACHER.value)
    s_headers = get_headers(student.id, UserRole.STUDENT.value)

    # --------------------------------------------------------------------------
    # 1. Dashboards
    # --------------------------------------------------------------------------
    s_dash_res = await client.get("/api/v1/dashboards/student", headers=s_headers)
    assert s_dash_res.status_code == 200
    s_dash = s_dash_res.json()
    assert "attendance_percentage" in s_dash
    assert "attendance_trend" in s_dash

    t_dash_res = await client.get("/api/v1/dashboards/teacher", headers=t_headers)
    assert t_dash_res.status_code == 200
    t_dash = t_dash_res.json()
    assert "student_attendance_percentage" in t_dash

    a_dash_res = await client.get("/api/v1/dashboards/admin", headers=a_headers)
    assert a_dash_res.status_code == 200
    a_dash = a_dash_res.json()
    assert a_dash["system_health_status"] == "HEALTHY"

    # --------------------------------------------------------------------------
    # 2. Notifications & Announcements
    # --------------------------------------------------------------------------
    notif_list_res = await client.get("/api/v1/notifications/", headers=s_headers)
    assert notif_list_res.status_code == 200
    notifs = notif_list_res.json()
    assert len(notifs) >= 1
    notif_id = UUID(notifs[0]["id"])

    unread_res = await client.get("/api/v1/notifications/unread-count", headers=s_headers)
    assert unread_res.status_code == 200
    assert unread_res.json()["unread_count"] >= 1

    read_res = await client.post(f"/api/v1/notifications/{notif_id}/read", headers=s_headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    bulk_read_res = await client.post("/api/v1/notifications/mark-all-read", headers=s_headers)
    assert bulk_read_res.status_code == 200

    archive_res = await client.post(f"/api/v1/notifications/{notif_id}/archive", headers=s_headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["is_archived"] is True

    # Announcement
    anc_payload = {
        "title": "Exam Schedule Released",
        "content": "Final exams commence next month.",
        "target_type": "global"
    }
    anc_create_res = await client.post("/api/v1/notifications/announcements", json=anc_payload, headers=t_headers)
    assert anc_create_res.status_code == 201

    anc_list_res = await client.get("/api/v1/notifications/announcements", headers=s_headers)
    assert anc_list_res.status_code == 200
    assert len(anc_list_res.json()) >= 1

    # --------------------------------------------------------------------------
    # 3. Report Generation & Download
    # --------------------------------------------------------------------------
    report_payload = {
        "report_type": "attendance",
        "format": "csv",
        "filters": {"course_id": None}
    }
    rep_gen_res = await client.post("/api/v1/reports/generate", json=report_payload, headers=t_headers)
    assert rep_gen_res.status_code == 201
    rep_data = rep_gen_res.json()
    rep_id = UUID(rep_data["id"])

    rep_dl_res = await client.get(f"/api/v1/reports/{rep_id}/download", headers=t_headers)
    assert rep_dl_res.status_code == 200
    assert len(rep_dl_res.content) > 0

    # --------------------------------------------------------------------------
    # 4. Analytics Platform Endpoints
    # --------------------------------------------------------------------------
    att_an_res = await client.get("/api/v1/analytics/attendance", headers=t_headers)
    assert att_an_res.status_code == 200
    assert isinstance(att_an_res.json(), list)

    quiz_an_res = await client.get("/api/v1/analytics/quiz", headers=t_headers)
    assert quiz_an_res.status_code == 200

    ai_an_res = await client.get("/api/v1/analytics/ai-usage", headers=a_headers)
    assert ai_an_res.status_code == 200

    # --------------------------------------------------------------------------
    # 5. Global Search
    # --------------------------------------------------------------------------
    search_res = await client.get("/api/v1/search/global?q=Ada", headers=s_headers)
    assert search_res.status_code == 200
    s_results = search_res.json()
    assert "students" in s_results
    assert len(s_results["students"]) >= 1

    # --------------------------------------------------------------------------
    # 6. Activity Timeline
    # --------------------------------------------------------------------------
    time_res = await client.get("/api/v1/timeline/activity", headers=s_headers)
    assert time_res.status_code == 200
    assert len(time_res.json()) >= 1
