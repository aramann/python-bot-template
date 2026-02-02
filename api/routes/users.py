"""
Эндпоинты для работы с пользователями.
"""

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_user, get_uow
from api.schemas import UserResponse
from common.db.postgres.uow import UnitOfWork

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: int = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Получить данные текущего пользователя."""
    user = await uow.users.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
