"""
Интеракторы для работы с базой данных.

Каждый интерактор отвечает за работу с определённой моделью.
"""

from common.db.postgres.interactors.user import UserInteractor

__all__ = [
    "UserInteractor",
]
