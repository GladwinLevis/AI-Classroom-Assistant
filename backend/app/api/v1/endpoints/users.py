from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user_id, RoleChecker
from app.models.user import UserRole
from app.schemas.user import UserResponse, UserUpdate
from app.repositories.user import UserRepository
from app.core.exceptions import EntityNotFoundException

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves authenticated user profile information."""
    repo = UserRepository(db)
    user = await repo.get(current_user_id)
    if not user:
        raise EntityNotFoundException("User not found.")
    return user


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    profile_update: UserUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Updates active user credentials or profile attributes."""
    repo = UserRepository(db)
    user = await repo.get(current_user_id)
    if not user:
        raise EntityNotFoundException("User not found.")
    return await repo.update(user, profile_update)


@router.get("/admin/users", response_model=list[UserResponse], dependencies=[Depends(RoleChecker([UserRole.ADMIN]))])
async def list_users_admin(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Admin-only path listing all active system users."""
    repo = UserRepository(db)
    return await repo.get_multi(skip=skip, limit=limit)
