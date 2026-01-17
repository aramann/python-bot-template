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
account_manager/
├── bot/                    # Логика бота
│   └── main.py
├── common/db/postgres/
│   ├── base.py             # BaseInteractor + Base для моделей
│   ├── models/             # SQLAlchemy модели
│   │   ├── __init__.py     # ⚠️ ИМПОРТЫ ВСЕХ МОДЕЛЕЙ (для Alembic!)
│   │   └── user.py
│   └── interactors/        # Работа с БД
│       ├── __init__.py
│       └── user.py
├── alembic/                # Миграции
├── data/                   # Persistent данные (Docker volume)
├── config.py               # Конфиг через pydantic-settings
├── Dockerfile
└── compose.yaml
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

Python 3.14 • PostgreSQL • SQLAlchemy 2.0 • Alembic • Pydantic Settings • pyTelegramBotAPI • Docker • UV
