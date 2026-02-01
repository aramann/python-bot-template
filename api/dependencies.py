"""
API Dependencies - аутентификация и общие зависимости.
"""

import json
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.auth.telegram import TelegramAuth
from common.db.postgres.interactors.user import UserInteractor
from config import config

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """
    Валидация Telegram WebApp init_data из Bearer токена.

    Шаги:
    1. Извлекает init_data из Bearer токена
    2. Валидирует HMAC-SHA256 подпись
    3. Проверяет срок действия (24 часа)
    4. Создаёт/обновляет пользователя в БД

    Returns:
        user_id: ID пользователя в БД

    Raises:
        HTTPException 401: Невалидный токен
        HTTPException 500: Ошибка создания пользователя
    """
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Debug token для разработки (формат: debug_token;user_id)
    if config.api.debug_token:
        parts = token.split(";")
        if parts[0] == config.api.debug_token and len(parts) == 2:
            return int(parts[1])

    # Парсим init_data
    try:
        parsed_data = TelegramAuth.parse_init_data(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid init data format",
        )

    # Проверяем обязательные поля
    if "hash" not in parsed_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing hash",
        )

    if "user" not in parsed_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user data",
        )

    # Валидируем подпись
    received_hash = parsed_data.pop("hash")
    if not TelegramAuth.validate_signature(parsed_data, received_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    # Проверяем срок действия
    if "auth_date" in parsed_data:
        if not TelegramAuth.check_expiration(parsed_data["auth_date"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Init data expired",
            )

    # Парсим данные пользователя
    try:
        user_data = json.loads(parsed_data["user"])
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data format",
        )

    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user ID",
        )

    # Создаём/получаем пользователя в БД
    try:
        user, _ = await UserInteractor.get_or_create(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
        )
        return user.id
    except Exception as e:
        logger.exception(f"Failed to create user: telegram_id={telegram_id}, error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error",
        )
