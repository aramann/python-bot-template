import asyncio
import logging

import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.handlers import StartHandler
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        logger.exception(exception)
        return True


bot = AsyncTeleBot(config.bot.token, exception_handler=ExceptionHandler())

# Создаём инстансы обработчиков
start_handler = StartHandler(bot)


# Регистрируем обработчики команд
@bot.message_handler(commands=["start"])
async def cmd_start(message: Message):
    """Команда /start"""
    await start_handler.handle(message)


async def main():
    print("Bot started...")
    await bot.infinity_polling()


if __name__ == "__main__":
    asyncio.run(main())
