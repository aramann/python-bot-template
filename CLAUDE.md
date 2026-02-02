# CLAUDE.md

Шаблон для Telegram ботов + FastAPI бэкенд для Mini App.

## Структура проекта

```
bot/                    # Telegram бот (PyTelegramBotAPI async)
  handlers/             # Обработчики команд (наследуются от BaseHandler)
api/                    # FastAPI для Mini App
  routes/               # Роутеры с эндпоинтами
  schemas/              # Pydantic схемы
  dependencies.py       # DI: сессия, UoW, аутентификация
common/                 # Общие модули
  db/postgres/
    models/             # SQLAlchemy модели
    interactors/        # Репозитории (CRUD)
    base.py             # Base, get_session()
    uow.py              # Unit of Work
  auth/telegram.py      # Валидация Telegram WebApp init_data
  cache.py              # Декоратор @cached для Redis
  redis.py              # Async Redis клиент
alembic/                # Миграции БД
config.py               # Pydantic Settings конфигурация
```

## Технологии

- Python 3.12+, uv (package manager)
- FastAPI + Uvicorn
- PyTelegramBotAPI (async)
- SQLAlchemy 2.0+ (async) + asyncpg
- Alembic (миграции)
- Redis (кэширование)
- Docker Compose

## Архитектура

**Паттерн Unit of Work + Repository:**

```
Request → get_db_session() → AsyncSession → UnitOfWork → Repository → Model
```

- `UnitOfWork` (`common/db/postgres/uow.py`) — контейнер репозиториев
- Репозитории (`common/db/postgres/interactors/`) — CRUD операции
- Сессия автоматически делает commit при успехе, rollback при ошибке

## Команды

```bash
# Зависимости
uv sync

# Миграции
uv run alembic revision --autogenerate -m "описание"
uv run alembic upgrade head
uv run alembic downgrade -1

# Запуск
uv run -m bot.main                                    # Бот
uv run uvicorn api.main:app --reload                  # API

# Docker
docker compose up --build -d
```

## Добавление новой модели

1. Создать модель в `common/db/postgres/models/`:

```python
from common.db.postgres.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    # ...
```

2. Импортировать в `common/db/postgres/models/__init__.py`

3. Создать репозиторий в `common/db/postgres/interactors/`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from common.db.postgres.models import Order


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: int) -> Order | None:
        return await self.session.get(Order, id)
```

4. Добавить в `UnitOfWork` (`common/db/postgres/uow.py`):

```python
self.orders = OrderRepository(session)
```

5. Сгенерировать миграцию:

```bash
uv run alembic revision --autogenerate -m "Add orders table"
uv run alembic upgrade head
```

## Добавление API эндпоинта

1. Создать роутер в `api/routes/`:

```python
from fastapi import APIRouter, Depends
from common.db.postgres.uow import UnitOfWork
from api.dependencies import get_uow

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}")
async def get_order(order_id: int, uow: UnitOfWork = Depends(get_uow)):
    return await uow.orders.get_by_id(order_id)
```

2. Подключить в `api/main.py`:

```python
from api.routes import orders

app.include_router(orders.router)
```

## Добавление обработчика бота

Создать в `bot/handlers/`:

```python
from bot.handlers.base import BaseHandler
from telebot.async_telebot import AsyncTeleBot


class MyHandler(BaseHandler):
    def register(self, bot: AsyncTeleBot):
        @bot.message_handler(commands=["mycommand"])
        async def handle(message):
            await self.handle(message)

    async def handle(self, message):
        # Используй async with get_session() as session:
        # uow = UnitOfWork(session)
        pass
```

Зарегистрировать в `bot/main.py`.

## Кэширование

```python
from common.cache import cached


@cached(ttl=300, key="user:{user_id}")
async def get_user(user_id: int):
# ...
```

## Конфигурация

Переменные в `.env` с разделителем `__`:

```
POSTGRES__USER, POSTGRES__PASSWORD, POSTGRES__HOST, POSTGRES__PORT, POSTGRES__DB
BOT__TOKEN
API__DEBUG, API__DEBUG_TOKEN, API__DOCS_SECRET
REDIS__HOST, REDIS__PORT, REDIS__DB
```

Доступ в коде:

```python
from config import config

config.bot.token
config.postgres.url
config.redis.url
```

## Аутентификация Mini App

- Bearer token в Authorization header = Telegram WebApp init_data
- Валидация через HMAC-SHA256 с bot token
- Debug режим: `API__DEBUG_TOKEN=secret;user_id`
- Зависимость `get_current_user()` возвращает User из БД
