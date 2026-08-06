import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.dashboard import GlobalSearchResponse
from app.services.search import SearchService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/global", response_model=GlobalSearchResponse)
async def execute_global_search(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes platform-wide search across students, teachers, assignments, quizzes, documents, courses, and announcements."""
    svc = SearchService(db)
    return await svc.global_search(q)
