"""Базовый класс для всех обработчиков"""

from telebot.async_telebot import AsyncTeleBot


class BaseHandler:
    """
    Базовый класс для всех обработчиков.

    Все хэндлеры наследуют этот класс и получают доступ к инстансу бота.
    """

    def __init__(self, bot: AsyncTeleBot):
        """
        Инициализация обработчика.

        Args:
            bot: Инстанс AsyncTeleBot
        """
        self.bot = bot
