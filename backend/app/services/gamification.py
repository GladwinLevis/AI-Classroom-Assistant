import logging
import uuid
from datetime import datetime
from typing import List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gamification import UserGamification
from app.models.user import User
from app.schemas.advanced import (
    UserGamificationResponse,
    BadgeItem,
    AchievementItem,
    LeaderboardEntry
)

logger = logging.getLogger(__name__)


class GamificationService:
    """
    Gamification & Achievement Platform service managing XP, levels, streaks, badges, and leaderboards.
    Dynamically computes scores and leaderboards from actual database records.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user_gamification(self, user_id: uuid.UUID) -> UserGamification:
        """Retrieves or creates user gamification record initialized at baseline state."""
        stmt = select(UserGamification).filter(UserGamification.user_id == user_id)
        res = await self.db.execute(stmt)
        record = res.scalars().first()

        if not record:
            record = UserGamification(
                user_id=user_id,
                xp_points=0,
                level=1,
                current_streak=0,
                longest_streak=0,
                badges=[],
                achievements=[]
            )
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)

        return record

    async def get_user_profile(self, user_id: uuid.UUID) -> UserGamificationResponse:
        """Retrieves gamification profile."""
        record = await self.get_or_create_user_gamification(user_id)
        
        badges = [
            BadgeItem(
                badge_id=b.get("badge_id", ""),
                name=b.get("name", ""),
                description=b.get("description", ""),
                icon=b.get("icon", "award"),
                unlocked_at=datetime.fromisoformat(b["unlocked_at"]) if isinstance(b.get("unlocked_at"), str) else (b.get("unlocked_at") or datetime.utcnow())
            )
            for b in (record.badges or [])
        ]

        achievements = [
            AchievementItem(
                achievement_id=a.get("achievement_id", ""),
                title=a.get("title", ""),
                xp_reward=a.get("xp_reward", 0),
                progress_percentage=a.get("progress_percentage", 0.0)
            )
            for a in (record.achievements or [])
        ]

        return UserGamificationResponse(
            user_id=record.user_id,
            xp_points=record.xp_points,
            level=record.level,
            current_streak=record.current_streak,
            longest_streak=record.longest_streak,
            badges=badges,
            achievements=achievements
        )

    async def get_leaderboard(self) -> List[LeaderboardEntry]:
        """Returns course leaderboard top performers dynamically from database records."""
        stmt = select(UserGamification, User).join(User, UserGamification.user_id == User.id).order_by(desc(UserGamification.xp_points)).limit(10)
        res = await self.db.execute(stmt)
        rows = res.all()

        leaderboard = []
        for idx, (gam, usr) in enumerate(rows, start=1):
            full_name = f"{usr.first_name} {usr.last_name}".strip()
            leaderboard.append(
                LeaderboardEntry(
                    rank=idx,
                    user_id=str(usr.id),
                    name=full_name if full_name else "User",
                    xp_points=gam.xp_points,
                    level=gam.level
                )
            )

        return leaderboard
