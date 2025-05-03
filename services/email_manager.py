# services/email_manager.py
import time
from typing import Any, Dict

from loguru import logger

from config import Settings
from schemas import EmailCategory

from .gemini_client import GeminiClient
from .imap_client import ImapClient
from .tg_bot import TelegramBot
from .tg_client import TelegramClient

# В будущем импортируем другие сервисы
# from .tg_client import TelegramClient

class EmailManager:
    """Менеджер для управления обработкой электронной почты"""

    def __init__(self, config: Settings):
        """
        Инициализация менеджера

        Args:
            config: Конфигурация из config.py
        """
        self.config = config
        self.imap_client = ImapClient(
            server=config.google.server,
            port=config.google.port,
            email_address=config.google.email,
            password=config.google.password
        )
        debug = config.MODE == "DEV"
        self.gemini_client = GeminiClient(api_key=config.gemini.api_key, debug=debug)
        self.tg_bot = TelegramBot(token=config.bot.token, client_id=config.bot.client_id)
        self.tg_client = TelegramClient(config.tg_client.api_id, config.tg_client.api_hash, config.tg_client.bot_name, config.tg_client.session_name)
        self.is_running = False

    def start(self):
        """Запуск обработки почты в цикле"""
        logger.info("Запуск менеджера обработки почты")

        # Подключаемся к IMAP серверу
        if not self.imap_client.connect():
            logger.error("Не удалось подключиться к IMAP серверу. Завершение работы.")
            return

        # В будущем подключаем другие сервисы
        if not self.tg_bot.start():
            logger.warning("Не удалось подключиться к Telegram API. Уведомления будут недоступны.")

        self.is_running = True

        try:
            while self.is_running:
                self.process_emails()

                # Ожидаем 60 секунд до следующей проверки
                logger.info("Ожидание 60 секунд до следующей проверки...")
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Работа скрипта остановлена пользователем")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            self.stop()

    def stop(self):
        """Остановка всех сервисов"""
        self.is_running = False

        # Закрываем соединение с IMAP
        if hasattr(self, 'imap_client'):
            self.imap_client.disconnect()

        # В будущем отключаем другие сервисы
        # if hasattr(self, 'tg_bot'):
        #     self.tg_bot.stop()
        # if hasattr(self, 'tg_client'):
        #     self.tg_client.disconnect()

        logger.info("Менеджер обработки почты остановлен")

    def process_emails(self):
        """Обработка непрочитанных писем"""
        logger.info("Начало обработки непрочитанных писем")

        # Выбираем папку "Входящие"
        if not self.imap_client.select_mailbox("INBOX"):
            logger.error("Не удалось выбрать папку INBOX")
            return

        # Получаем список непрочитанных писем
        email_ids = self.imap_client.get_unseen_emails_ids()
        logger.info(f"Найдено {len(email_ids)} непрочитанных писем")

        if not email_ids:
            return

        # Обрабатываем каждое непрочитанное письмо
        for email_id in email_ids:
            # Получаем письмо по ID
            email_data = self.imap_client.get_email_by_id(email_id)

            if not email_data:
                logger.warning(f"Не удалось получить письмо с ID {email_id}")
                continue

            # Обрабатываем письмо
            self._process_single_email(email_data)

            # Помечаем как прочитанное
            self.imap_client.mark_as_read(email_id)


    def _process_single_email(self, email_data: Dict[str, Any]):
        """
        Обработка одного письма

        Args:
            email_data: данные письма
        """
        # Очищаем данные письма от HTML и форматируем
        from .html_cleaner import EmailCleaner
        cleaned_email = EmailCleaner.clean_email_data(email_data)
        subject = cleaned_email.get('subject', "Без темы")
        # Выполняем классификацию письма через Gemini
        classification = None
        if "pioner" in email_data["from"]:
            classification = EmailCategory.MESSAGE

        if not classification:
            classification = self.gemini_client.classify_email(
                subject=cleaned_email['subject'],
                body=cleaned_email['text_content']
            )

        logger.info(f"Письмо классифицировано как: {classification}")

        if classification in [EmailCategory.MESSAGE, EmailCategory.OTHER, EmailCategory.SUPPORT]:
            self.tg_bot.send_message(self._create_alert_message(cleaned_email, email_data))
            logger.info(f"Отправлено уведомление о письме: {subject}")
        elif classification == EmailCategory.PAYMENT:
            payment_data = self.gemini_client.extract_payment_data(subject, cleaned_email["text_content"])
            sender = cleaned_email.get('sender_name', email_data.get("from", "Неизвестный отправитель"))
            self.tg_client.send_payment_data(payment_data, sender)
        elif classification == EmailCategory.NOTICE:
            ... # TODO Надо поискать кнопку отписать и попытаться отписаться
        else: # classification == EmailCategory.IMPORTANT
            ... # Оставим место, вдруг потом захочется добавить логики, пока ее не будет
        logger.info(f"Письмо обработано: {cleaned_email['subject']}")
        return True  # Помечаем как прочитанное


    def _create_alert_message(self, cleaned_email: dict, email_data: dict, provider: str = "gmail"):
        """
        Создает текст уведомления для отправки в Telegram

        Args:
            cleaned_email: очищенные данные письма
            email_data: исходные данные письма

        Returns:
            Текст сообщения для Telegram
        """
        try:
            sender = cleaned_email.get('sender_name', email_data.get("from", "Неизвестный отправитель"))
            subject = cleaned_email.get('subject', email_data.get("subject", 'Без темы'))

            # Получаем ссылку на поиск письма
            # Используем Gmail по умолчанию, можно изменить на "yandex" при необходимости
            email_link = self._get_email_search_link(email_data, provider)

            # Создаем минималистичное сообщение
            message = f"<b>📧 Сообщение от: {sender}</b>\n\n"

            # Добавляем тему с ссылкой или без
            if email_link:
                message += f"<a href='{email_link}'>{subject}</a>"
            else:
                message += subject

            return message
        except Exception as e:
            logger.error(f"Ошибка при создании текста уведомления: {e}")
            return f"Новое письмо от {email_data.get('from', 'Неизвестный')}"

    def _get_email_search_link(self, email_data: Dict[str, Any], provider: str = "gmail") -> str:
        """
        Создает ссылку на поиск письма в почтовом клиенте

        Args:
            email_data: данные письма
            provider: почтовый провайдер ("gmail" или "yandex")

        Returns:
            URL для поиска письма
        """
        try:
            # Получаем тему письма
            subject = email_data.get("subject", "")
            if not subject:
                return ""

            # Кодируем тему для использования в URL
            import urllib.parse
            encoded_subject = urllib.parse.quote_plus(subject)

            # Формируем ссылку в зависимости от провайдера
            if provider.lower() == "gmail":
                return f"https://mail.google.com/mail/u/0/#search/{encoded_subject}"
            elif provider.lower() == "yandex":
                return f"https://mail.yandex.ru/#search?request={encoded_subject}"
            else:
                logger.warning(f"Неизвестный почтовый провайдер: {provider}")
                return ""

        except Exception as e:
            logger.error(f"Ошибка при создании ссылки на поиск письма: {e}")
            return ""


    def _get_message_id(self, email_data: dict) -> str:
        """
        Извлекает Message-ID из данных письма

        Args:
            email_data: данные письма

        Returns:
            Message-ID или пустая строка
        """
        try:
            # Пробуем получить из уже извлеченных данных
            if email_data.get('message_id'):
                return email_data['message_id']

            # Если нет, пробуем извлечь из raw_message
            if 'raw_message' in email_data and hasattr(email_data['raw_message'], 'get'):
                message_id = email_data['raw_message'].get('Message-ID')
                if message_id:
                    return message_id

            # Последняя попытка - посмотреть все заголовки
            if 'raw_message' in email_data:
                for name, value in email_data['raw_message'].items():
                    if name.lower() == 'message-id':
                        return value

            # Не нашли Message-ID
            return ''
        except Exception as e:
            logger.error(f"Ошибка при извлечении Message-ID: {e}")
            return ''