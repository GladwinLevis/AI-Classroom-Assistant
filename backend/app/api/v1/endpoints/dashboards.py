import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import (
    StudentDashboardResponse,
    TeacherDashboardResponse,
    AdminDashboardResponse
)
from app.services.dashboard import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/student", response_model=StudentDashboardResponse)
async def get_student_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves student dashboard analytics, schedule, assignments, quiz stats, and study progress."""
    svc = DashboardService(db)
    return await svc.get_student_dashboard(current_user.id)


@router.get("/teacher", response_model=TeacherDashboardResponse)
async def get_teacher_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves teacher dashboard analytics, attendance trends, pending reviews, and class performance."""
    svc = DashboardService(db)
    return await svc.get_teacher_dashboard(current_user.id)


@router.get("/admin", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves admin system health, active user stats, storage, and AI usage metrics."""
    svc = DashboardService(db)
    return await svc.get_admin_dashboard()
