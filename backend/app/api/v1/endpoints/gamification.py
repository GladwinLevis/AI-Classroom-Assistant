from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.advanced import UserGamificationResponse, LeaderboardEntry
from app.services.gamification import GamificationService

router = APIRouter()


@router.get("/profile", response_model=UserGamificationResponse, status_code=status.HTTP_200_OK)
async def get_gamification_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves student XP, level, streak, badges, and achievements."""
    svc = GamificationService(db)
    return await svc.get_user_profile(current_user.id)


@router.get("/leaderboard", response_model=List[LeaderboardEntry], status_code=status.HTTP_200_OK)
async def get_course_leaderboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves course leaderboard top performers."""
    svc = GamificationService(db)
    return await svc.get_leaderboard()
