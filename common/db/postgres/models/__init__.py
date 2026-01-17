"""
Модели базы данных.

Все модели должны быть импортированы здесь для корректной работы Alembic миграций.
"""

from common.db.postgres.models.user import User

__all__ = [
    "User",
]
