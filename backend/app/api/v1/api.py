from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    attendance,
    notes,
    chat,
    assignments,
    quizzes,
    health,
    dashboards,
    notifications,
    reports,
    analytics,
    search,
    timeline,
    advanced_ai,
    gamification,
    academic_calendar,
    recommendations,
    insights
)

api_router = APIRouter()

# Include version 1 routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["User Profiles"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(notes.router, prefix="/notes", tags=["Notes & Summaries"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Chatbot"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["Assignments"])
api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quiz Generation"])

api_router.include_router(health.router, prefix="/health", tags=["Health Checks"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards"])
api_router.include_router(dashboards.router, prefix="/dashboard", tags=["Dashboards"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications & Announcements"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reporting Engine"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics Platform"])
api_router.include_router(search.router, prefix="/search", tags=["Global Search"])
api_router.include_router(timeline.router, prefix="/timeline", tags=["Activity Timeline"])

# Phase 11 Routers
api_router.include_router(advanced_ai.router, prefix="/ai", tags=["Advanced Explainable AI"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["Gamification & Achievements"])
api_router.include_router(academic_calendar.router, prefix="/calendar", tags=["Academic Calendar & Reminders"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Learning Recommendation Engine"])
api_router.include_router(insights.router, prefix="/insights", tags=["AI Predictive Insights & Hybrid Search"])
