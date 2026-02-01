"""
База для работы с PostgreSQL.

Предоставляет:
- Base для ORM моделей
- get_session() context manager для работы с сессией
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from config import config

Base = declarative_base()

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def _init_db() -> None:
    """Инициализация engine и session_maker."""
    global _engine, _session_maker

    if _engine is None:
        _engine = create_async_engine(
            config.database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        _session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager для работы с сессией.

    Использование:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(1)

    Автоматически коммитит при успехе, откатывает при ошибке.
    """
    _init_db()

    async with _session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Закрыть соединения с БД."""
    global _engine, _session_maker

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_maker = None
