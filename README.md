# Telegram Bot Template

Шаблон для Telegram ботов с PostgreSQL, SQLAlchemy, Alembic и Docker.

## Быстрый старт

### Docker (рекомендуется)

```bash
cp .env.example .env  # заполни переменные
docker compose up --build -d
docker compose run --rm bot alembic upgrade head
docker compose logs -f bot
```

### Локально

```bash
cp .env.example .env
uv sync
createdb account_manager
uv run alembic upgrade head
uv run -m bot.main
```

## Структура

```
project/
├── bot/                    # Telegram бот
│   ├── main.py             # Точка входа бота
│   └── handlers/           # Обработчики команд
├── api/                    # FastAPI для Mini App
│   ├── dependencies.py     # DI: сессия, UoW, аутентификация
│   └── routes/             # Эндпоинты
├── common/
│   ├── auth/               # Telegram WebApp валидация
│   ├── cache.py            # Декоратор @cached для Redis
│   ├── redis.py            # Redis клиент
│   └── db/postgres/
│       ├── base.py         # get_session() + Base
│       ├── uow.py          # Unit of Work
│       ├── models/         # SQLAlchemy модели
│       └── interactors/    # Репозитории
├── alembic/                # Миграции
├── config.py               # Конфиг (pydantic-settings)
├── Dockerfile
└── compose.yaml
```

## Архитектура: Unit of Work + Dependency Injection

### Зачем это нужно?

- **Одна транзакция** на весь запрос (несколько операций — один commit)
- **Легко тестировать** (можно мокать сессию)
- **Меньше соединений** к БД

### Как это работает

```
HTTP Request
     ↓
get_db_session()     → AsyncSession (одна на запрос)
     ↓
get_uow()            → UnitOfWork(session)
     ↓                   ├── users: UserRepository
Эндпоинт                 ├── orders: OrderRepository
     ↓                   └── ... (все репозитории)
     ↓
Автоматический commit/rollback
```

### Unit of Work

`common/db/postgres/uow.py` — контейнер для всех репозиториев:

```python
class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.orders = OrderRepository(session)
        # Все репозитории используют одну сессию
```

### Использование в FastAPI

```python
from api.dependencies import get_uow
from common.db.postgres.uow import UnitOfWork

@router.post("/order")
async def create_order(uow: UnitOfWork = Depends(get_uow)):
    user = await uow.users.get_by_id(1)
    order = await uow.orders.create(user_id=user.id, total=100)
    await uow.logs.create(action="order_created")
    # Один commit в конце — все операции атомарны
```

### Использование в боте

```python
from common.db.postgres.base import get_session
from common.db.postgres.uow import UnitOfWork

async def handle(self, message: Message):
    async with get_session() as session:
        uow = UnitOfWork(session)
        user, created = await uow.users.get_or_create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
```

## Как добавить новый репозиторий

### 1. Создай модель

`common/db/postgres/models/order.py`:

```python
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from common.db.postgres.base import Base

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    total: Mapped[int]
```

### 2. Импортируй в `models/__init__.py`

```python
from common.db.postgres.models.user import User
from common.db.postgres.models.order import Order  # ← добавь

__all__ = ["User", "Order"]
```

**КРИТИЧНО:** Без этого Alembic не увидит модель!

### 3. Создай репозиторий

`common/db/postgres/interactors/order.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.postgres.models.order import Order

class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, total: int) -> Order:
        order = Order(user_id=user_id, total=total)
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order
```

### 4. Добавь в Unit of Work

`common/db/postgres/uow.py`:

```python
from common.db.postgres.interactors.order import OrderRepository

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.orders = OrderRepository(session)  # ← добавь
```

### 5. Создай миграцию

```bash
uv run alembic revision --autogenerate -m "Add orders"
uv run alembic upgrade head
```

### 6. Используй

```python
@router.get("/orders/{order_id}")
async def get_order(order_id: int, uow: UnitOfWork = Depends(get_uow)):
    order = await uow.orders.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404)
    return order
```

## Как добавить хэндлер бота

### Структура хэндлеров

```
bot/
├── main.py                 # Точка входа + регистрация обработчиков
└── handlers/
    ├── __init__.py
    ├── base.py             # Базовый класс BaseHandler
    └── start.py            # Пример: обработчик /start
```

### Создание нового хэндлера

1. Создай файл `bot/handlers/menu.py`:

```python
from telebot.types import Message, CallbackQuery
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.handlers.base import BaseHandler
from common.db.postgres.base import get_session
from common.db.postgres.uow import UnitOfWork


class MenuHandler(BaseHandler):
    """Обработчик главного меню"""

    async def show_menu(self, message: Message):
        """Показать главное меню"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Профиль", callback_data="profile"),
            InlineKeyboardButton("Настройки", callback_data="settings"),
        )

        await self.bot.send_message(
            message.chat.id,
            "Выберите действие:",
            reply_markup=markup,
        )

    async def on_profile_callback(self, call: CallbackQuery):
        """Callback: нажатие на кнопку Профиль"""
        async with get_session() as session:
            uow = UnitOfWork(session)
            user = await uow.users.get_by_telegram_id(call.from_user.id)

        await self.bot.answer_callback_query(call.id)
        await self.bot.send_message(
            call.message.chat.id,
            f"Ваш профиль: {user.first_name}",
        )
```

2. Добавь экспорт в `bot/handlers/__init__.py`:

```python
from bot.handlers.menu import MenuHandler

__all__ = ["BaseHandler", "StartHandler", "MenuHandler"]
```

3. Зарегистрируй в `bot/main.py`:

```python
from bot.handlers import StartHandler, MenuHandler

start_handler = StartHandler(bot)
menu_handler = MenuHandler(bot)


@bot.message_handler(commands=["menu"])
async def cmd_menu(message: Message):
    await menu_handler.show_menu(message)


@bot.callback_query_handler(func=lambda call: call.data == "profile")
async def callback_profile(call: CallbackQuery):
    await menu_handler.on_profile_callback(call)
```

## API (FastAPI)

### Структура

```
api/
├── dependencies.py      # get_db_session, get_uow, get_current_user
└── routes/
    └── users.py         # Пример роутера
```

### Запуск

```bash
uv run uvicorn api.main:app --reload   # API
uv run -m bot.main                      # Бот (отдельно)
```

### Добавление роутера

1. Создай `api/routes/orders.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_current_user, get_uow
from common.db.postgres.uow import UnitOfWork

router = APIRouter(prefix="/orders", tags=["Orders"])


class OrderResponse(BaseModel):
    id: int
    total: int

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    user_id: int = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Список заказов текущего пользователя."""
    orders = await uow.orders.get_by_user_id(user_id)
    return orders


@router.post("/", response_model=OrderResponse)
async def create_order(
    total: int,
    user_id: int = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_uow),
):
    """Создать заказ."""
    order = await uow.orders.create(user_id=user_id, total=total)
    return order
```

2. Подключи в `api/main.py`:

```python
from api.routes import users, orders

app.include_router(users.router)
app.include_router(orders.router)
```

### Аутентификация

API использует Telegram WebApp init_data:

```python
from api.dependencies import get_current_user

@router.get("/protected")
async def protected_endpoint(user_id: int = Depends(get_current_user)):
    # user_id — ID в БД (не telegram_id!)
    return {"user_id": user_id}
```

**Debug режим:** `API__DEBUG_TOKEN=secret123` → Bearer токен `secret123;1` где `1` — user_id.

## Redis и кэширование

### Подключение

Redis подключается в `api/main.py` через lifespan:

```python
from common.redis import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.connect()
    yield
    await redis_client.disconnect()
```

### Использование

```python
from common.redis import redis_client

await redis_client.set("key", "value", ex=3600)
value = await redis_client.get("key")

await redis_client.set_json("user:123", {"name": "John"}, ex=300)
data = await redis_client.get_json("user:123")
```

### Кэширование через декоратор

```python
from common.cache import cached, invalidate

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @cached(ttl=300, key="user:{user_id}", model=User)
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(...)
        return result.scalar_one_or_none()

    async def update(self, user_id: int, **kwargs) -> User:
        ...
        await invalidate(f"user:{user_id}")
```

- `ttl` — время жизни в секундах
- `key` — шаблон ключа (подставляются аргументы)
- `model` — ORM модель для десериализации
- Graceful fallback: если Redis недоступен — работает напрямую с БД

## Конфигурация

В `.env` используй двойное подчёркивание для групп:

```bash
POSTGRES__USER=user
POSTGRES__PASSWORD=pass
POSTGRES__HOST=localhost     # локально
POSTGRES__HOST=postgres      # Docker
BOT__TOKEN=123:ABC...
API__DEBUG_TOKEN=secret123   # для тестов
REDIS__HOST=localhost
```

Доступ в коде:

```python
from config import config

config.postgres.url
config.bot.token
config.api.debug_token
```

## Docker команды

```bash
# Запуск/остановка
docker compose up -d
docker compose down
docker compose logs -f bot

# Миграции
docker compose run --rm bot alembic upgrade head
docker compose run --rm bot alembic revision --autogenerate -m "msg"
```

### PostgreSQL в Docker

Добавь в `compose.yaml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES__USER}
      POSTGRES_PASSWORD: ${POSTGRES__PASSWORD}
      POSTGRES_DB: ${POSTGRES__DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  bot:
    depends_on:
      - postgres

volumes:
  postgres_data:
```

## Стек

Python 3.14 • FastAPI • PostgreSQL • Redis • SQLAlchemy 2.0 • Alembic • Pydantic Settings • pyTelegramBotAPI • Docker • UV
