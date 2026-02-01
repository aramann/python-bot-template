"""
Пример интерактора для работы с пользователями.

Создавай интеракторы по аналогии с этим.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.postgres.base import BaseInteractor
from common.db.postgres.models.user import User


class UserInteractor(BaseInteractor):
    """Интерактор для работы с пользователями"""

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int) -> Optional[User]:
        """
        Получить пользователя по telegram_id

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            User или None если не найден
        """
        async with cls.get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def create(
        cls,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> User:
        """
        Создать нового пользователя

        Args:
            telegram_id: ID пользователя в Telegram
            username: Username пользователя
            first_name: Имя
            last_name: Фамилия

        Returns:
            Созданный пользователь
        """
        async with cls.get_session() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user

    @classmethod
    async def get_or_create(
        cls,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> tuple[User, bool]:
        """
        Получить существующего пользователя или создать нового.

        Если пользователь существует - обновляет его данные (username, first_name, last_name).

        Args:
            telegram_id: ID пользователя в Telegram
            username: Username пользователя
            first_name: Имя
            last_name: Фамилия

        Returns:
            Кортеж (пользователь, был_создан)
        """
        async with cls.get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()

            if user:
                # Обновляем данные если изменились
                needs_update = False

                if username is not None and user.username != username:
                    user.username = username
                    needs_update = True

                if first_name is not None and user.first_name != first_name:
                    user.first_name = first_name
                    needs_update = True

                if last_name is not None and user.last_name != last_name:
                    user.last_name = last_name
                    needs_update = True

                if needs_update:
                    session.add(user)
                    await session.flush()
                    await session.refresh(user)

                return user, False

            # Создаём нового пользователя
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            return user, True

    @classmethod
    async def get_by_id(cls, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID в БД

        Args:
            user_id: ID пользователя в БД

        Returns:
            User или None если не найден
        """
        async with cls.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def update(cls, user_id: int, **kwargs) -> Optional[User]:
        """
        Обновить данные пользователя

        Args:
            user_id: ID пользователя в БД
            **kwargs: Поля для обновления

        Returns:
            Обновлённый пользователь или None
        """
        async with cls.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return None

            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            await session.flush()
            await session.refresh(user)
            return user
