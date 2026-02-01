"""
Декоратор для кэширования в Redis.

Использование:
    @cached(ttl=300, key="user:{user_id}")
    async def get_by_id(self, user_id: int) -> User | None:
        ...
"""

import functools
import inspect
import json
import logging
from datetime import datetime
from typing import Callable, Type

logger = logging.getLogger(__name__)


def _serialize(obj) -> str:
    """Сериализация объекта в JSON."""
    if obj is None:
        return json.dumps(None)

    if hasattr(obj, "__table__"):  # SQLAlchemy model
        data = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        # datetime -> isoformat
        for k, v in data.items():
            if isinstance(v, datetime):
                data[k] = v.isoformat()
        data["__model__"] = obj.__class__.__name__
        return json.dumps(data)

    return json.dumps(obj)


def _deserialize(data: str, model: Type = None):
    """Десериализация из JSON."""
    obj = json.loads(data)

    if obj is None:
        return None

    if model and isinstance(obj, dict) and "__model__" in obj:
        obj.pop("__model__")
        # datetime fields
        for k, v in obj.items():
            if isinstance(v, str) and "T" in v:
                try:
                    obj[k] = datetime.fromisoformat(v)
                except ValueError:
                    pass
        instance = model.__new__(model)
        for k, v in obj.items():
            setattr(instance, k, v)
        return instance

    return obj


def cached(ttl: int, key: str, model: Type = None):
    """
    Декоратор для кэширования.

    Работает как с методами инстанса (self), так и с classmethod (cls).

    Args:
        ttl: Время жизни в секундах
        key: Шаблон ключа, например "user:{user_id}"
        model: ORM модель для десериализации (опционально)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем сигнатуру функции
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())

            # Пропускаем self/cls (первый параметр)
            if param_names and param_names[0] in ("self", "cls"):
                param_names = param_names[1:]
                func_args = args[1:]  # пропускаем self/cls
            else:
                func_args = args

            # Формируем словарь параметров
            params = dict(zip(param_names, func_args))
            params.update(kwargs)

            # Формируем ключ кэша
            cache_key = key.format(**params)

            # Пытаемся получить из кэша
            try:
                from common.redis import redis_client

                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    return _deserialize(cached_data, model)
            except Exception:
                pass

            # Вызываем оригинальную функцию
            result = await func(*args, **kwargs)

            # Сохраняем в кэш
            if result is not None:
                try:
                    from common.redis import redis_client

                    await redis_client.set(cache_key, _serialize(result), ex=ttl)
                except Exception:
                    pass

            return result

        return wrapper

    return decorator


async def invalidate(key: str) -> None:
    """Инвалидировать кэш."""
    try:
        from common.redis import redis_client

        await redis_client.delete(key)
    except Exception:
        pass
