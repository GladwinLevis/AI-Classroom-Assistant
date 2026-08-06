import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, StudentProfile, UserRole
from app.models.security import Role
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_complete_phase11_advanced_ai_and_enterprise_flow(client: AsyncClient, db_session: AsyncSession):
    """
    End-to-End integration test covering Phase 11 features:
    1. Multi-Provider AI Query with Explainability & Source Citations
    2. Gamification Profile, XP, Badges & Leaderboard Rankings
    3. Academic Calendar Events & Smart Reminders
    4. Learning Recommendation Engine & Daily Goals
    5. Predictive AI Learning Insights & Drop Risk Analysis
    6. FAISS Vector + BM25 Hybrid Search
    """
    # Create test user directly in DB
    student_user = User(
        email="phase11_student@example.com",
        hashed_password="hashed_pass_mock",
        first_name="Phase11",
        last_name="Student",
        is_active=True,
        is_verified=True
    )
    db_session.add(student_user)
    await db_session.flush()

    student_profile = StudentProfile(
        user_id=student_user.id,
        roll_number="ROLL-12345",
        academic_year="2026"
    )
    db_session.add(student_profile)
    await db_session.commit()

    token = create_access_token(data={"sub": str(student_user.id), "role": UserRole.STUDENT.value})
    headers = {"Authorization": f"Bearer {token}"}

    # --------------------------------------------------------------------------
    # 2. Multi-Provider Explainable AI Query
    # --------------------------------------------------------------------------
    ai_res = await client.post(
        "/api/v1/ai/query-explainable?prompt=Explain%20RAG%20Architecture&context=RAG%20uses%20vector%20databases",
        headers=headers
    )
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert ai_data["confidence_score"] > 0.8
    assert "reasoning_summary" in ai_data
    assert len(ai_data["source_references"]) > 0

    # --------------------------------------------------------------------------
    # 3. Gamification Profile & Leaderboard
    # --------------------------------------------------------------------------
    gam_res = await client.get("/api/v1/gamification/profile", headers=headers)
    assert gam_res.status_code == 200
    gam_data = gam_res.json()
    assert gam_data["xp_points"] >= 0
    assert gam_data["level"] >= 1

    leaderboard_res = await client.get("/api/v1/gamification/leaderboard", headers=headers)
    assert leaderboard_res.status_code == 200
    assert isinstance(leaderboard_res.json(), list)

    # --------------------------------------------------------------------------
    # 4. Academic Calendar Events & Smart Reminders
    # --------------------------------------------------------------------------
    cal_res = await client.get("/api/v1/calendar/events", headers=headers)
    assert cal_res.status_code == 200
    assert isinstance(cal_res.json(), list)

    create_cal_res = await client.post("/api/v1/calendar/events", json={
        "title": "Study Group Review",
        "description": "Review Graph Theory",
        "event_type": "study",
        "start_time": "2026-07-25T10:00:00Z"
    }, headers=headers)
    assert create_cal_res.status_code == 201

    reminders_res = await client.get("/api/v1/calendar/reminders", headers=headers)
    assert reminders_res.status_code == 200
    assert isinstance(reminders_res.json(), list)

    # --------------------------------------------------------------------------
    # 5. Learning Recommendation Engine
    # --------------------------------------------------------------------------
    rec_res = await client.get("/api/v1/recommendations/learning-path", headers=headers)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert isinstance(rec_data["weak_concepts"], list)
    assert isinstance(rec_data["learning_path"], list)

    # --------------------------------------------------------------------------
    # 6. Predictive AI Insights & Hybrid Search
    # --------------------------------------------------------------------------
    ins_res = await client.get("/api/v1/insights/student-risk", headers=headers)
    assert ins_res.status_code == 200
    ins_data = ins_res.json()
    assert "drop_risk" in ins_data

    search_res = await client.get("/api/v1/insights/search/hybrid?q=embeddings", headers=headers)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data["results"]) > 0
