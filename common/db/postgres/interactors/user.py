"""
Репозиторий для работы с пользователями.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.cache import cached, invalidate
from common.db.postgres.models.user import User


class UserRepository:
    """
    Репозиторий для работы с пользователями.

    Использование:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(1)
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    @cached(ttl=300, key="user:{user_id}", model=User)
    async def get_by_id(self, user_id: int) -> User | None:
        """Получить пользователя по ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @cached(ttl=300, key="user:tg:{telegram_id}", model=User)
    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Получить пользователя по telegram_id."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def _invalidate_user(self, user: User) -> None:
        """Инвалидировать все кэши пользователя."""
        await invalidate(f"user:{user.id}")
        await invalidate(f"user:tg:{user.telegram_id}")

    async def create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """Создать нового пользователя."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> tuple[User, bool]:
        """
        Получить или создать пользователя.

        Обновляет данные если они изменились.

        Returns:
            tuple[User, bool]: (пользователь, создан ли новый)
        """
        user = await self.get_by_telegram_id(telegram_id)

        if user:
            needs_update = False

            if username is not None and user.username != username:
                needs_update = True
            if first_name is not None and user.first_name != first_name:
                needs_update = True
            if last_name is not None and user.last_name != last_name:
                needs_update = True

            if needs_update:
                # Получаем свежий объект из БД для обновления
                result = await self.session.execute(
                    select(User).where(User.id == user.id)
                )
                db_user = result.scalar_one()
                db_user.username = username
                db_user.first_name = first_name
                db_user.last_name = last_name
                await self.session.flush()
                await self.session.refresh(db_user)
                await self._invalidate_user(db_user)
                return db_user, False

            return user, False

        # Создаём нового
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user, True

    async def update(self, user_id: int, **kwargs) -> User | None:
        """Обновить данные пользователя."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.session.flush()
        await self.session.refresh(user)
        await self._invalidate_user(user)
        return user
