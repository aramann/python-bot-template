"""
Эндпоинты для работы с пользователями.
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencies import get_current_user
from common.db.postgres.interactors.user import UserInteractor

router = APIRouter(prefix="/users", tags=["Users"])


class UserResponse(BaseModel):
    """Ответ с данными пользователя"""

    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: str


@router.get("/me", response_model=UserResponse)
async def get_me(user_id: int = Depends(get_current_user)):
    """Получить данные текущего пользователя."""
    user = await UserInteractor.get_by_id(user_id)
    return UserResponse.model_validate(user)
