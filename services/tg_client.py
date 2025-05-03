"""
Клиент для отправки сообщений через пользовательский аккаунт Telegram
"""
import datetime
from typing import Dict, Any
from loguru import logger
from pyrogram import Client # type: ignore

class TelegramClient:
    """Клиент для отправки сообщений через пользовательский аккаунт Telegram"""

    def __init__(self, api_id: str, api_hash: str, bot_username: str, session_name: str):
        """
        Инициализация Telegram клиента

        Args:
            api_id: API ID Telegram
            api_hash: API Hash Telegram
            bot_username: Имя бота для отправки сообщений (без @)
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_username = bot_username
        self.session_name = session_name
        logger.info("TelegramClient инициализирован")

    def send_payment_data(self, payment_data: Dict[str, Any], sender: str) -> bool:
        """
        Отправляет структурированные данные о платеже в Telegram

        Args:
            payment_data: Данные о платеже
            email_date: Дата письма (если не указана в payment_data)

        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            # Получаем данные платежа
            date = datetime.datetime.now().isoformat()
            payment_type = payment_data.get("payment_type", "")
            currency = payment_data.get('currency', '')
            amount = payment_data.get('amount', '')
            item = payment_data.get('item', '')

            # Формируем строку для бота в формате: |дата|валюта|сумма|услуга|регулярный|
            message = f"| {date} | {payment_type} | {currency} | {amount} | {item} | {sender} |"

            # Отправляем сообщение
            return self.send_message(message)

        except Exception as e:
            logger.error(f"Ошибка при отправке данных о платеже: {e}")
            return False

    def send_message(self, text: str) -> bool:
        """
        Отправляет сообщение в Telegram

        Args:
            text: Текст сообщения
            chat_id: ID чата для отправки (если не указан, используется bot_username)

        Returns:
            True в случае успеха, False в случае ошибки
        """
        # Определяем получателя
        recipient = self.bot_username

        try:
            # Используем контекстный менеджер для автоматического подключения и отключения
            app = Client(f"sessions/{self.session_name}", self.api_id, self.api_hash)

            with app:
                app.send_message(recipient, text) # type: ignore
                logger.info(f"Сообщение успешно отправлено в Telegram")
                return True

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            return False