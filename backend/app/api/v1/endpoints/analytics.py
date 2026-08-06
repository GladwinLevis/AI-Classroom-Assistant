import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import RechartsSeriesData
from app.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/attendance", response_model=List[RechartsSeriesData])
async def get_attendance_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns attendance trend data formatted for Recharts components."""
    svc = AnalyticsService(db)
    return await svc.get_attendance_analytics()


@router.get("/quiz", response_model=List[RechartsSeriesData])
async def get_quiz_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns quiz score distribution formatted for Recharts components."""
    svc = AnalyticsService(db)
    return await svc.get_quiz_analytics()


@router.get("/assignment", response_model=List[RechartsSeriesData])
async def get_assignment_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns assignment submission statistics formatted for Recharts components."""
    svc = AnalyticsService(db)
    return await svc.get_assignment_analytics()


@router.get("/ai-usage", response_model=List[RechartsSeriesData])
async def get_ai_usage_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns AI feature engagement statistics formatted for Recharts components."""
    svc = AnalyticsService(db)
    return await svc.get_ai_usage_analytics()
