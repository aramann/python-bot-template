"""
Репозитории для работы с базой данных.

Каждый репозиторий отвечает за работу с определённой моделью.
"""

from common.db.postgres.interactors.user import UserRepository

__all__ = [
    "UserRepository",
]
