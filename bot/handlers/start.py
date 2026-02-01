"""Обработчик команды /start"""

from telebot.types import Message

from bot.handlers.base import BaseHandler
from common.db.postgres.interactors.user import UserInteractor


class StartHandler(BaseHandler):
    """Обработчик команды /start"""

    async def handle(self, message: Message):
        """
        Обработчик команды /start.

        Создаёт пользователя в БД если его нет и отправляет приветствие.
        """
        telegram_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        user, created = await UserInteractor.get_or_create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        if created:
            text = f"Привет, {first_name or 'друг'}! Добро пожаловать!"
        else:
            text = f"С возвращением, {first_name or 'друг'}!"

        await self.bot.send_message(message.chat.id, text)
