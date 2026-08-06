from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.advanced import AIExplainableResponse
from app.services.ai_provider import MultiProviderAIService

router = APIRouter()


@router.post("/query-explainable", response_model=AIExplainableResponse, status_code=status.HTTP_200_OK)
async def query_explainable_ai(
    prompt: str,
    context: str = "",
    current_user: User = Depends(get_current_active_user)
):
    """Executes AI prompt with multi-provider fallbacks and explainability metrics."""
    svc = MultiProviderAIService()
    return await svc.query_with_explainability(prompt, context)
