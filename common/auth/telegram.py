"""
Валидация Telegram WebApp init_data.

Используется для аутентификации пользователей Mini App через API.
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl

from config import config


class TelegramAuth:
    """Helper для валидации Telegram WebApp authentication data."""

    @staticmethod
    def validate_signature(data: dict[str, Any], received_hash: str) -> bool:
        """
        Валидация подписи init_data.

        Алгоритм:
        1. Создаём secret key: HMAC-SHA256("WebAppData", bot_token)
        2. Создаём data check string: отсортированные key=value через \\n
        3. Вычисляем HMAC-SHA256 от data check string с secret key
        4. Сравниваем с полученным хэшем

        Args:
            data: Распарсенные данные (без hash)
            received_hash: Хэш от клиента

        Returns:
            True если подпись валидна
        """
        bot_token = config.bot.token
        if not bot_token:
            raise ValueError("bot_token not configured")

        # Step 1: Create secret key
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256,
        ).digest()

        # Step 2: Create data check string
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(data.items())
        )

        # Step 3: Compute hash
        computed_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

        # Step 4: Compare (constant-time)
        return hmac.compare_digest(computed_hash, received_hash)

    @staticmethod
    def parse_init_data(init_data: str) -> dict[str, Any]:
        """Парсинг raw init_data string в словарь."""
        return dict(parse_qsl(init_data))

    @staticmethod
    def extract_user_data(user_json: str) -> dict[str, Any] | None:
        """Извлечение данных пользователя из JSON строки."""
        try:
            return json.loads(user_json)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def check_expiration(auth_date: str, max_age_seconds: int = 86400) -> bool:
        """
        Проверка срока действия auth_date.

        Args:
            auth_date: Unix timestamp в виде строки
            max_age_seconds: Максимальный возраст в секундах (по умолчанию 24 часа)

        Returns:
            True если данные не истекли
        """
        try:
            auth_timestamp = int(auth_date)
            current_timestamp = int(datetime.now(timezone.utc).timestamp())
            return (current_timestamp - auth_timestamp) <= max_age_seconds
        except (ValueError, TypeError):
            return False
