import asyncio
from telebot.async_telebot import AsyncTeleBot

from config import config

bot = AsyncTeleBot(config.bot.token)

@bot.message_handler(commands=['start'])
async def start_handler(message):
    await bot.reply_to(message, "hello")

async def main():
    print("Bot started...")
    await bot.infinity_polling()

if __name__ == '__main__':
    asyncio.run(main())
