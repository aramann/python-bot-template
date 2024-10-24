import telebot

import config
from modules import SQLighter


bot = telebot.TeleBot(config.bot_token)
db = SQLighter(config.postrges_db, config.postrges_user, config.postrges_password, config.postrges_host, config.postrges_port)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello! I'm a bot!")


bot.infinity_polling()