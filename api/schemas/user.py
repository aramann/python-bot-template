from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Ответ с данными пользователя."""

    id: int
    telegram_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
