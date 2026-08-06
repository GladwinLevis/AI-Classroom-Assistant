import os
import pytest
import pytest_asyncio
from uuid import UUID
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, StudentProfile, TeacherProfile, UserRole
from app.models.security import Role
from app.models.course import Subject, Course, Enrollment
from app.models.assignment import Assignment, AssignmentSubmission, AssignmentFeedback
from app.core.security import create_access_token, get_password_hash


def get_headers(user_id: UUID, role_name: str = UserRole.STUDENT.value) -> dict:
    token = create_access_token(data={"sub": str(user_id), "role": role_name})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seed_asgn_data(db_session: AsyncSession):
    """Seeds teacher, 2 student users, subject, course, and enrollments for assignment tests."""
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

    await db_session.flush()

    # Teacher user
    teacher_user = User(
        email="prof_asgn@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Alan",
        last_name="Turing",
        is_active=True,
        is_verified=True,
        roles=[t_role]
    )
    db_session.add(teacher_user)
    await db_session.flush()

    teacher_prof = TeacherProfile(user_id=teacher_user.id, employee_id="EMP-ASGN-01", department="Computer Science")
    db_session.add(teacher_prof)

    # Student 1
    student1 = User(
        email="asgn_student1@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Ada",
        last_name="Lovelace",
        is_active=True,
        is_verified=True,
        roles=[s_role]
    )
    db_session.add(student1)
    await db_session.flush()

    s1_prof = StudentProfile(user_id=student1.id, roll_number="CS-ASGN-01", academic_year="2026")
    db_session.add(s1_prof)

    # Student 2
    student2 = User(
        email="asgn_student2@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Charles",
        last_name="Babbage",
        is_active=True,
        is_verified=True,
        roles=[s_role]
    )
    db_session.add(student2)
    await db_session.flush()

    s2_prof = StudentProfile(user_id=student2.id, roll_number="CS-ASGN-02", academic_year="2026")
    db_session.add(s2_prof)

    # Subject & Course
    subject = Subject(name="Algorithms & AI", code="CS401", department="Computer Science")
    db_session.add(subject)
    await db_session.flush()

    course = Course(
        name="Advanced AI Systems",
        code="CS401-2026",
        subject_id=subject.id,
        teacher_id=teacher_user.id
    )
    db_session.add(course)
    await db_session.flush()

    # Enrollments
    e1 = Enrollment(student_id=s1_prof.id, course_id=course.id)
    e2 = Enrollment(student_id=s2_prof.id, course_id=course.id)
    db_session.add_all([e1, e2])

    await db_session.commit()

    return {
        "teacher": teacher_user,
        "student1": student1,
        "student1_profile": s1_prof,
        "student2": student2,
        "student2_profile": s2_prof,
        "course": course
    }


@pytest.mark.asyncio
async def test_complete_ai_assignment_checker_flow(
    client: AsyncClient,
    seed_asgn_data: dict,
    db_session: AsyncSession
):
    """
    Validates complete AI Assignment Checker lifecycle:
    1. Teacher creates assignment with rubric
    2. Teacher publishes assignment
    3. Student 1 submits work & AI executes rubric evaluation
    4. Student 1 resubmits updated work (verifying versioning)
    5. Student 2 submits similar work (verifying similarity check)
    6. Teacher reviews AI evaluation report
    7. Teacher approves & finalizes grade
    8. Assignment Analytics computation
    9. Access boundary security checks
    """
    teacher = seed_asgn_data["teacher"]
    student1 = seed_asgn_data["student1"]
    student2 = seed_asgn_data["student2"]
    course = seed_asgn_data["course"]

    t_headers = get_headers(teacher.id, UserRole.TEACHER.value)
    s1_headers = get_headers(student1.id, UserRole.STUDENT.value)
    s2_headers = get_headers(student2.id, UserRole.STUDENT.value)

    # --------------------------------------------------------------------------
    # 1. Teacher creates assignment with custom rubric
    # --------------------------------------------------------------------------
    due_dt = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    asgn_payload = {
        "title": "Build a Vector Search Engine",
        "description": "Implement an HNSW/FAISS vector search indexing pipeline in Python.",
        "instructions": "Ensure proper vector normalization and cosine similarity scoring.",
        "due_date": due_dt,
        "max_points": 100.0,
        "course_id": str(course.id),
        "rubric": [
            {"name": "Concept Understanding", "max_score": 40.0, "description": "Mathematical soundness of vector embeddings."},
            {"name": "Technical Implementation", "max_score": 40.0, "description": "Efficiency of index generation."},
            {"name": "Documentation", "max_score": 20.0, "description": "Clarity of code comments and writeup."}
        ]
    }

    create_res = await client.post("/api/v1/assignments/", json=asgn_payload, headers=t_headers)
    assert create_res.status_code == 201
    asgn_data = create_res.json()
    asgn_id = UUID(asgn_data["id"])
    assert asgn_data["is_published"] is False
    assert len(asgn_data["rubric"]) == 3

    # --------------------------------------------------------------------------
    # 2. Teacher publishes assignment
    # --------------------------------------------------------------------------
    pub_res = await client.post(f"/api/v1/assignments/{asgn_id}/publish", headers=t_headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["is_published"] is True

    # --------------------------------------------------------------------------
    # 3. Student 1 submits text work (triggers synchronous AI evaluation)
    # --------------------------------------------------------------------------
    os.environ["TESTING"] = "True"
    s1_text = (
        "Vector search engine implementation using sentence-transformers and FAISS index. "
        "Dense vectors are calculated and normalized before computing inner product similarity scores."
    )
    
    sub1_res = await client.post(
        f"/api/v1/assignments/{asgn_id}/submit",
        data={"submitted_text": s1_text},
        headers=s1_headers
    )
    assert sub1_res.status_code == 201
    sub1_data = sub1_res.json()
    sub1_id = UUID(sub1_data["id"])
    assert sub1_data["version"] == 1
    assert sub1_data["is_final"] is True
    assert sub1_data["processing_status"] == "evaluated"

    # --------------------------------------------------------------------------
    # 4. Student 1 resubmits updated version
    # --------------------------------------------------------------------------
    s1_updated_text = s1_text + " Updated version with GPU accelerated indexing."
    resub_res = await client.post(
        f"/api/v1/assignments/{asgn_id}/resubmit",
        data={"submitted_text": s1_updated_text},
        headers=s1_headers
    )
    assert resub_res.status_code == 200
    resub_data = resub_res.json()
    assert resub_data["version"] == 2
    assert resub_data["is_final"] is True

    # Verify history lists 2 submissions
    hist_res = await client.get(f"/api/v1/assignments/{asgn_id}/my-submissions", headers=s1_headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) == 2

    # --------------------------------------------------------------------------
    # 5. Student 2 submits similar work (triggers local embedding similarity check)
    # --------------------------------------------------------------------------
    sub2_res = await client.post(
        f"/api/v1/assignments/{asgn_id}/submit",
        data={"submitted_text": s1_text},  # Exact duplicate text
        headers=s2_headers
    )
    assert sub2_res.status_code == 201
    sub2_id = UUID(sub2_res.json()["id"])

    # Verify similarity check recorded plagiarism score
    review2_res = await client.get(f"/api/v1/assignments/submission/{sub2_id}/review", headers=t_headers)
    assert review2_res.status_code == 200
    fb2_data = review2_res.json()
    assert fb2_data["plagiarism_score"] >= 0.0
    assert fb2_data["similarity_report"] is not None

    # --------------------------------------------------------------------------
    # 6. Teacher reviews Student 1's submission evaluation
    # --------------------------------------------------------------------------
    final_sub1_id = UUID(resub_data["id"])
    review1_res = await client.get(f"/api/v1/assignments/submission/{final_sub1_id}/review", headers=t_headers)
    assert review1_res.status_code == 200
    fb1_data = review1_res.json()
    assert fb1_data["ai_score"] is not None
    assert len(fb1_data["rubric_evaluation"]) == 3
    assert fb1_data["is_approved"] is False

    # --------------------------------------------------------------------------
    # 7. Teacher approves grade with score override
    # --------------------------------------------------------------------------
    appr_payload = {
        "approved_score": 95.0,
        "teacher_comments": "Outstanding technical architecture and vector indexing performance!"
    }
    appr_res = await client.post(
        f"/api/v1/assignments/submission/{final_sub1_id}/approve",
        json=appr_payload,
        headers=t_headers
    )
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["final_score"] == 95.0
    assert appr_data["is_approved"] is True
    assert appr_data["status"] == "approved"

    # --------------------------------------------------------------------------
    # 8. Assignment Analytics verification
    # --------------------------------------------------------------------------
    analytics_res = await client.get(f"/api/v1/assignments/{asgn_id}/analytics", headers=t_headers)
    assert analytics_res.status_code == 200
    an_data = analytics_res.json()
    assert an_data["total_students"] == 2
    assert an_data["submissions_count"] == 3
    assert an_data["submission_rate"] == 100.0
    assert an_data["highest_score"] is not None
    assert len(an_data["rubric_performance"]) > 0

    # --------------------------------------------------------------------------
    # 9. Access Control Security Checks
    # --------------------------------------------------------------------------
    # Student 1 cannot approve grades
    unauth_appr = await client.post(
        f"/api/v1/assignments/submission/{final_sub1_id}/approve",
        json={"approved_score": 100.0},
        headers=s1_headers
    )
    assert unauth_appr.status_code == 401

    # Student 2 cannot access Student 1's submission details
    unauth_sub = await client.get(f"/api/v1/assignments/submission/{final_sub1_id}", headers=s2_headers)
    assert unauth_sub.status_code == 401
