from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.advanced import LearningRecommendationResponse
from app.services.recommendation import LearningRecommendationEngine

router = APIRouter()


@router.get("/learning-path", response_model=LearningRecommendationResponse, status_code=status.HTTP_200_OK)
async def get_personalized_learning_path(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves personalized learning recommendations, weak concepts, and daily goals."""
    engine = LearningRecommendationEngine(db)
    return await engine.generate_recommendations(current_user.id)
