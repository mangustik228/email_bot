# services/tg_bot.py
import requests
from loguru import logger

class TelegramBot:
    """Клиент для отправки сообщений через Telegram бота"""

    def __init__(self, token: str, client_id: int):
        """
        Инициализация Telegram бота

        Args:
            token: API токен бота
            client_id: ID пользователя для отправки сообщений
        """
        self.token = token
        self.client_id = client_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        logger.info("TelegramBot инициализирован")

    def start(self):
        """Запуск бота (проверка соединения)"""
        try:
            # Просто делаем тестовый запрос для проверки токена
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_name = data.get("result", {}).get("username", "Unknown")
                    logger.info(f"TelegramBot запущен, подключен к боту @{bot_name}")
                    return True

            logger.error(f"Не удалось подключиться к Telegram API: {response.status_code} - {response.text}")
            return False

        except Exception as e:
            logger.error(f"Ошибка при запуске TelegramBot: {e}")
            return False

    def stop(self):
        """Остановка бота"""
        # Ничего делать не нужно, так как мы не держим постоянное соединение
        logger.info("TelegramBot остановлен")

    def send_message(self, text: str) -> bool:
        """
        Отправляет сообщение пользователю

        Args:
            text: Текст сообщения

        Returns:
            True в случае успеха, False в случае ошибки
        """
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.client_id,
                "text": text,
                "parse_mode": "HTML"
            }

            # Создаем новое соединение для каждого запроса
            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                logger.info(f"Сообщение успешно отправлено")
                return True
            else:
                logger.error(f"Ошибка при отправке сообщения: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
            return False