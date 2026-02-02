"""
Главная точка входа для API.

Запуск:
    uv run uvicorn api.main:app --reload
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import users
from common.redis import redis_client
from config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.

    Startup: инициализация ресурсов
    Shutdown: корректное закрытие ресурсов
    """
    # Startup
    print("API starting...")
    await redis_client.connect()

    yield

    # Shutdown
    print("API shutting down...")
    await redis_client.disconnect()


# Настройка путей к документации
docs_url = "/docs"
redoc_url = "/redoc"
openapi_url = "/openapi.json"

if config.api.docs_secret:
    # Скрытая документация по секретному пути
    docs_url = f"/{config.api.docs_secret}/docs"
    redoc_url = f"/{config.api.docs_secret}/redoc"
    openapi_url = f"/{config.api.docs_secret}/openapi.json"

app = FastAPI(
    title="My App",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутеры
app.include_router(users.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
