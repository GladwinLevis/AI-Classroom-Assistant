import os
import pytest
import pytest_asyncio
from uuid import UUID
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, StudentProfile, TeacherProfile, UserRole
from app.models.security import Role
from app.models.course import Subject, Course, Enrollment
from app.models.quiz import Quiz, QuizQuestion, QuizAttempt, QuestionBank
from app.core.security import create_access_token, get_password_hash


def get_headers(user_id: UUID, role_name: str = UserRole.STUDENT.value) -> dict:
    token = create_access_token(data={"sub": str(user_id), "role": role_name})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def seed_quiz_data(db_session: AsyncSession):
    """Seeds teacher, 2 student users, subject, course, and enrollments for quiz testing."""
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
        email="prof_quiz@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Grace",
        last_name="Hopper",
        is_active=True,
        is_verified=True,
        roles=[t_role]
    )
    db_session.add(teacher_user)
    await db_session.flush()

    teacher_prof = TeacherProfile(user_id=teacher_user.id, employee_id="EMP-QUIZ-01", department="Computer Science")
    db_session.add(teacher_prof)

    # Student 1
    student1 = User(
        email="quiz_student1@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="John",
        last_name="von Neumann",
        is_active=True,
        is_verified=True,
        roles=[s_role]
    )
    db_session.add(student1)
    await db_session.flush()

    s1_prof = StudentProfile(user_id=student1.id, roll_number="CS-QUIZ-01", academic_year="2026")
    db_session.add(s1_prof)

    # Student 2
    student2 = User(
        email="quiz_student2@example.com",
        hashed_password=get_password_hash("Password123!"),
        first_name="Claude",
        last_name="Shannon",
        is_active=True,
        is_verified=True,
        roles=[s_role]
    )
    db_session.add(student2)
    await db_session.flush()

    s2_prof = StudentProfile(user_id=student2.id, roll_number="CS-QUIZ-02", academic_year="2026")
    db_session.add(s2_prof)

    # Subject & Course
    subject = Subject(name="Information Theory & AI", code="CS501", department="Computer Science")
    db_session.add(subject)
    await db_session.flush()

    course = Course(
        name="Assessment Architecture",
        code="CS501-2026",
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
async def test_complete_ai_quiz_assessment_engine_flow(
    client: AsyncClient,
    seed_quiz_data: dict,
    db_session: AsyncSession
):
    """
    Validates complete AI Quiz Generator and Assessment Engine lifecycle:
    1. AI generates quiz from topic across Bloom's Taxonomy levels
    2. Teacher publishes quiz
    3. Student 1 starts attempt & saves progress
    4. Student 1 submits attempt (verifying auto & subjective grading)
    5. Student 2 submits attempt (verifying leaderboard rankings)
    6. Adaptive Learning Recommendations for student
    7. Teacher Quiz Analytics & Leaderboard
    8. Question Bank Search & Filtering
    """
    teacher = seed_quiz_data["teacher"]
    student1 = seed_quiz_data["student1"]
    student2 = seed_quiz_data["student2"]
    course = seed_quiz_data["course"]

    t_headers = get_headers(teacher.id, UserRole.TEACHER.value)
    s1_headers = get_headers(student1.id, UserRole.STUDENT.value)
    s2_headers = get_headers(student2.id, UserRole.STUDENT.value)

    # --------------------------------------------------------------------------
    # 1. AI Quiz Generation from Topic
    # --------------------------------------------------------------------------
    os.environ["TESTING"] = "True"
    gen_payload = {
        "topic": "Entropy & Information Theory",
        "num_questions": 3,
        "difficulty": "mixed",
        "blooms_level": ["Remember", "Understand", "Apply"],
        "question_types": ["mcq", "true_false", "short_answer"],
        "course_id": str(course.id)
    }

    gen_res = await client.post("/api/v1/quizzes/generate", json=gen_payload, headers=t_headers)
    assert gen_res.status_code == 201
    quiz_data = gen_res.json()
    quiz_id = UUID(quiz_data["id"])
    assert quiz_data["is_published"] is False
    assert len(quiz_data["questions"]) == 3

    questions = quiz_data["questions"]
    q1_id = UUID(questions[0]["id"])
    q2_id = UUID(questions[1]["id"])
    q3_id = UUID(questions[2]["id"])

    # --------------------------------------------------------------------------
    # 2. Teacher publishes quiz
    # --------------------------------------------------------------------------
    pub_res = await client.post(f"/api/v1/quizzes/{quiz_id}/publish", headers=t_headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["is_published"] is True

    # --------------------------------------------------------------------------
    # 3. Student 1 starts quiz attempt & auto-saves progress
    # --------------------------------------------------------------------------
    start1_res = await client.post(f"/api/v1/quizzes/{quiz_id}/start", headers=s1_headers)
    assert start1_res.status_code == 201
    att1_data = start1_res.json()
    att1_id = UUID(att1_data["id"])
    assert att1_data["status"] == "in_progress"

    save_payload = {"progress_data": {str(q1_id): "High efficiency processing"}}
    save_res = await client.post(f"/api/v1/quizzes/attempt/{att1_id}/save", json=save_payload, headers=s1_headers)
    assert save_res.status_code == 200

    # --------------------------------------------------------------------------
    # 4. Student 1 submits attempt (auto evaluation)
    # --------------------------------------------------------------------------
    sub1_payload = {
        "answers": [
            {"question_id": str(q1_id), "selected_option": questions[0]["correct_answer"]},
            {"question_id": str(q2_id), "selected_option": questions[1]["correct_answer"]},
            {"question_id": str(q3_id), "provided_answer": "The workflow initializes context and executes processing."}
        ]
    }
    sub1_res = await client.post(f"/api/v1/quizzes/attempt/{att1_id}/submit", json=sub1_payload, headers=s1_headers)
    assert sub1_res.status_code == 200
    sub1_data = sub1_res.json()
    assert sub1_data["status"] == "evaluated"
    assert sub1_data["score"] > 0
    assert len(sub1_data["answers"]) == 3

    # --------------------------------------------------------------------------
    # 5. Student 2 starts and submits attempt
    # --------------------------------------------------------------------------
    start2_res = await client.post(f"/api/v1/quizzes/{quiz_id}/start", headers=s2_headers)
    att2_id = UUID(start2_res.json()["id"])

    sub2_payload = {
        "answers": [
            {"question_id": str(q1_id), "selected_option": "Wrong Option"},
            {"question_id": str(q2_id), "selected_option": questions[1]["correct_answer"]}
        ]
    }
    sub2_res = await client.post(f"/api/v1/quizzes/attempt/{att2_id}/submit", json=sub2_payload, headers=s2_headers)
    assert sub2_res.status_code == 200

    # --------------------------------------------------------------------------
    # 6. Adaptive Learning Recommendations for Student 1
    # --------------------------------------------------------------------------
    rec_res = await client.get("/api/v1/quizzes/adaptive-recommendations", headers=s1_headers)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert "accuracy_percentage" in rec_data
    assert "suggested_difficulty" in rec_data

    # --------------------------------------------------------------------------
    # 7. Teacher Analytics & Leaderboard
    # --------------------------------------------------------------------------
    an_res = await client.get(f"/api/v1/quizzes/{quiz_id}/analytics", headers=t_headers)
    assert an_res.status_code == 200
    assert an_res.json()["total_attempts"] == 2

    lb_res = await client.get(f"/api/v1/quizzes/{quiz_id}/leaderboard", headers=t_headers)
    assert lb_res.status_code == 200
    lb_data = lb_res.json()
    assert len(lb_data) == 2
    assert lb_data[0]["rank"] == 1

    # --------------------------------------------------------------------------
    # 8. Question Bank Search & Filtering
    # --------------------------------------------------------------------------
    qb_res = await client.get("/api/v1/quizzes/question-bank/search?topic=Entropy", headers=t_headers)
    assert qb_res.status_code == 200
    assert len(qb_res.json()) >= 3
