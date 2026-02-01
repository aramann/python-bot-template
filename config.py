from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    """Настройки PostgreSQL"""

    user: str = Field(..., description="PostgreSQL username")
    password: str = Field(..., description="PostgreSQL password")
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    db: str = Field(..., description="PostgreSQL database name")

    @computed_field
    @property
    def url(self) -> str:
        """Генерирует database URL для SQLAlchemy"""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.db}?async_fallback=True"
        )


class TelegramBotConfig(BaseModel):
    """Настройки Telegram бота"""

    token: str = Field(..., description="Telegram bot token")


class ApiConfig(BaseModel):
    """Настройки API"""

    debug: bool = Field(default=False, description="Debug mode")
    debug_token: str | None = Field(default=None, description="Debug token for development")
    docs_secret: str | None = Field(default=None, description="Secret path for API docs (None = public)")


class Config(BaseSettings):
    """Главная конфигурация приложения с автоматической загрузкой из .env"""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
        env_nested_delimiter='__'
    )

    # Группы настроек
    postgres: DatabaseConfig = Field(default_factory=lambda: DatabaseConfig(
        user="",
        password="",
        db=""
    ))
    bot: TelegramBotConfig = Field(default_factory=lambda: TelegramBotConfig(token=""))
    api: ApiConfig = Field(default_factory=ApiConfig)

    @property
    def database_url(self) -> str:
        """Алиас для обратной совместимости"""
        return self.postgres.url


# Создаём синглтон конфига
config = Config()
