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
│   ├── dependencies.py     # Аутентификация
│   └── routes/             # Эндпоинты
├── common/
│   ├── auth/               # Telegram WebApp валидация
│   └── db/postgres/
│       ├── base.py         # BaseInteractor + Base
│       ├── models/         # SQLAlchemy модели
│       └── interactors/    # Работа с БД
├── alembic/                # Миграции
├── main.py                 # Точка входа API
├── config.py               # Конфиг (pydantic-settings)
├── Dockerfile
└── compose.yaml
```

## Как добавить хэндлер

### Структура хэндлеров

```
bot/
├── main.py                 # Точка входа + регистрация обработчиков
└── handlers/
    ├── __init__.py         # Экспорты
    ├── base.py             # Базовый класс BaseHandler
    └── start.py            # Пример: обработчик /start
```

### Создание нового хэндлера

1. Создай файл `bot/handlers/menu.py`:

```python
from telebot.types import Message, CallbackQuery
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.handlers.base import BaseHandler


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
        await self.bot.answer_callback_query(call.id)
        await self.bot.send_message(call.message.chat.id, "Ваш профиль")
```

2. Добавь экспорт в `bot/handlers/__init__.py`:

```python
from bot.handlers.menu import MenuHandler

__all__ = ["BaseHandler", "StartHandler", "MenuHandler"]
```

3. Зарегистрируй в `bot/main.py`:

```python
from bot.handlers import StartHandler, MenuHandler

# Создаём инстансы обработчиков
start_handler = StartHandler(bot)
menu_handler = MenuHandler(bot)


@bot.message_handler(commands=["menu"])
async def cmd_menu(message: Message):
    await menu_handler.show_menu(message)


@bot.callback_query_handler(func=lambda call: call.data == "profile")
async def callback_profile(call: CallbackQuery):
    await menu_handler.on_profile_callback(call)
```

### FSM (Finite State Machine)

Для многошаговых сценариев используй состояния:

1. Создай `bot/states.py`:

```python
from telebot.asyncio_handler_backends import State, StatesGroup


class FormStates(StatesGroup):
    """Состояния для формы"""
    name_input = State()
    email_input = State()
```

2. Добавь storage в `bot/main.py`:

```python
from telebot.asyncio_storage import StateMemoryStorage

storage = StateMemoryStorage()
bot = AsyncTeleBot(config.bot.token, state_storage=storage)
```

3. Используй в хэндлере:

```python
from bot.states import FormStates


class FormHandler(BaseHandler):

    async def start_form(self, message: Message):
        """Начать заполнение формы"""
        await self.bot.set_state(
            message.from_user.id,
            FormStates.name_input,
            message.chat.id,
        )
        await self.bot.send_message(message.chat.id, "Введите имя:")

    async def on_name_input(self, message: Message):
        """Обработка ввода имени"""
        async with self.bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["name"] = message.text

        await self.bot.set_state(
            message.from_user.id,
            FormStates.email_input,
            message.chat.id,
        )
        await self.bot.send_message(message.chat.id, "Теперь введите email:")

    async def on_email_input(self, message: Message):
        """Обработка ввода email"""
        async with self.bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            name = data["name"]
            email = message.text

        await self.bot.delete_state(message.from_user.id, message.chat.id)
        await self.bot.send_message(
            message.chat.id,
            f"Готово! Имя: {name}, Email: {email}",
        )
```

4. Зарегистрируй FSM-обработчики:

```python
@bot.message_handler(state=FormStates.name_input)
async def handle_name_input(message: Message):
    await form_handler.on_name_input(message)


@bot.message_handler(state=FormStates.email_input)
async def handle_email_input(message: Message):
    await form_handler.on_email_input(message)
```

## API (FastAPI)

Для Mini App или внешних интеграций есть FastAPI.

### Структура

```
api/
├── __init__.py
├── dependencies.py      # Аутентификация (validate Telegram init_data)
└── routes/
    ├── __init__.py
    └── users.py         # Пример роутера
common/auth/
├── __init__.py
└── telegram.py          # Валидация Telegram WebApp
main.py                  # Точка входа FastAPI
```

### Запуск

```bash
# API
uv run uvicorn api.main:app --reload

# Бот (отдельный процесс)
uv run -m bot.main
```

### Добавление роутера

1. Создай `api/routes/items.py`:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.dependencies import get_current_user

router = APIRouter(prefix="/items", tags=["Items"])


class ItemResponse(BaseModel):
    id: int
    name: str


@router.get("/", response_model=list[ItemResponse])
async def list_items(user_id: int = Depends(get_current_user)):
    """Список items текущего пользователя."""
    # Используй интерактор для работы с БД
    return []


@router.post("/", response_model=ItemResponse)
async def create_item(
    name: str,
    user_id: int = Depends(get_current_user),
):
    """Создать item."""
    return ItemResponse(id=1, name=name)
```

2. Добавь в `api/routes/__init__.py`:

```python
from api.routes import users, items

__all__ = ["users", "items"]
```

3. Подключи в `main.py`:

```python
from api.routes import users, items

app.include_router(users.router, prefix="/api")
app.include_router(items.router, prefix="/api")
```

### Аутентификация

API использует Telegram WebApp init_data для аутентификации:

```python
from api.dependencies import get_current_user

@router.get("/protected")
async def protected_endpoint(user_id: int = Depends(get_current_user)):
    # user_id - это ID пользователя в БД (не telegram_id!)
    return {"user_id": user_id}
```

**Debug режим:** В `.env` установи `API__DEBUG_TOKEN=secret123`, затем в запросах используй Bearer токен `secret123;1` где `1` - user_id.

### Скрытая документация

Для продакшена скрой документацию:

```bash
# .env
API__DOCS_SECRET=MySecretPath123
```

Документация будет доступна по `/MySecretPath123/docs` вместо `/docs`.

### Lifespan (инициализация ресурсов)

В `main.py` есть lifespan для инициализации/закрытия ресурсов:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis = await aioredis.from_url("redis://localhost")
    app.state.redis = redis

    yield

    # Shutdown
    await redis.close()
```

## Как добавить новую модель

1. Создай модель `common/db/postgres/models/account.py`
2. **Импортируй в `models/__init__.py`** (иначе Alembic не увидит!)
3. Создай интерактор `common/db/postgres/interactors/account.py`
4. Импортируй в `interactors/__init__.py`
5. Миграции:
```bash
alembic revision --autogenerate -m "Add accounts"
alembic upgrade head
```

## Конфигурация

В `.env` используй двойное подчёркивание для групп:

```bash
POSTGRES__USER=user
POSTGRES__PASSWORD=pass
POSTGRES__HOST=localhost     # для локального запуска
POSTGRES__HOST=postgres      # для Docker с PostgreSQL
BOT__TOKEN=123:ABC...
```

Доступ в коде:
```python
from config import config

config.postgres.url
config.bot.token
```

## Важные моменты

### Интеракторы - stateless

Используем `@classmethod` т.к. интеракторы не хранят состояние:
```python
class UserInteractor(BaseInteractor):
    @classmethod
    async def get_by_id(cls, user_id: int):
        async with cls.get_session() as session:
            ...

# Вызов без создания объекта
user = await UserInteractor.get_by_id(123)
```

### Импорты моделей для Alembic

**КРИТИЧНО:** Все модели должны быть в `models/__init__.py`:
```python
from common.db.postgres.models.user import User
from common.db.postgres.models.account import Account

__all__ = ["User", "Account"]
```

Иначе Alembic не увидит модели при генерации миграций.

## Docker команды

```bash
# Запуск/остановка
docker compose up -d
docker compose down
docker compose logs -f bot

# Миграции
docker compose run --rm bot alembic upgrade head
docker compose run --rm bot alembic revision --autogenerate -m "msg"

# Выполнить команду
docker compose exec bot <command>
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
    restart: unless-stopped

  bot:
    depends_on:
      - postgres

volumes:
  postgres_data:
```

И в `.env`: `POSTGRES__HOST=postgres`

## Основные команды

```bash
# Зависимости
uv add <package>
uv sync

# Миграции
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Запуск
uv run -m bot.main
```

## Стек

Python 3.14 • FastAPI • PostgreSQL • SQLAlchemy 2.0 • Alembic • Pydantic Settings • pyTelegramBotAPI • Docker • UV
