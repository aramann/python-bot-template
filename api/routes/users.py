"""
Эндпоинты для работы с пользователями.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_current_user, get_uow
from common.db.postgres.uow import UnitOfWork

router = APIRouter(prefix="/users", tags=["Users"])


class UserResponse(BaseModel):
    """Ответ с данными пользователя"""

    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


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
