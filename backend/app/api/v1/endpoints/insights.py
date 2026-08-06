from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.advanced import StudentLearningInsights, HybridSearchResponse
from app.services.ai_insights import AIInsightsService
from app.services.advanced_search import HybridSearchService

router = APIRouter()


@router.get("/student-risk", response_model=StudentLearningInsights, status_code=status.HTTP_200_OK)
async def get_student_predictive_insights(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves predictive learning velocity and student drop-risk analysis."""
    svc = AIInsightsService(db)
    return await svc.get_student_insights(current_user.id)


@router.get("/search/hybrid", response_model=HybridSearchResponse, status_code=status.HTTP_200_OK)
async def execute_hybrid_search(
    q: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes FAISS vector + BM25 keyword hybrid search."""
    svc = HybridSearchService(db)
    return await svc.search(q)
