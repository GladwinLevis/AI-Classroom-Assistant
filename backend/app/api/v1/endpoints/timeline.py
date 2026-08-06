import logging
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import TimelineEventResponse
from app.services.timeline import TimelineService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/activity", response_model=List[TimelineEventResponse])
async def get_activity_timeline(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves activity timeline logs for the current user."""
    svc = TimelineService(db)
    return await svc.get_user_timeline(current_user.id, limit)
