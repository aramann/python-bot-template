"""
Redis клиент с connection pooling.

Использование:
    from common.redis import redis_client

    # В lifespan
    await redis_client.connect()
    yield
    await redis_client.disconnect()

    # В коде
    await redis_client.set("key", "value", ex=3600)
    value = await redis_client.get("key")
"""

import json
from typing import Any

from redis.asyncio import Redis, ConnectionPool

from config import config


class RedisClient:
    """Async Redis клиент с connection pooling."""

    def __init__(self):
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None

    async def connect(self) -> None:
        """Подключение к Redis."""
        self._pool = ConnectionPool.from_url(
            config.redis.url,
            max_connections=10,
            decode_responses=True,
        )
        self._client = Redis(connection_pool=self._pool)
        # Проверяем подключение
        await self._client.ping()
        print(f"Redis connected: {config.redis.host}:{config.redis.port}")

    async def disconnect(self) -> None:
        """Отключение от Redis."""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.disconnect()
        print("Redis disconnected")

    @property
    def client(self) -> Redis:
        """Получить Redis клиент."""
        if not self._client:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._client

    # Shortcut методы
    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def get_json(self, key: str) -> Any | None:
        """Получить JSON значение."""
        value = await self.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_json(self, key: str, value: Any, ex: int | None = None) -> None:
        """Сохранить JSON значение."""
        await self.set(key, json.dumps(value), ex=ex)

    async def ping(self) -> bool:
        """Проверка подключения к Redis."""
        try:
            if self._client:
                await self._client.ping()
                return True
        except Exception:
            pass
        return False


# Синглтон клиент
redis_client = RedisClient()
