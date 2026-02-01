import asyncio

from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.handlers import StartHandler
from config import config

bot = AsyncTeleBot(config.bot.token)

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
