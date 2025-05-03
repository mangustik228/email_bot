# services/imap_client.py
import imaplib
import email
from email.header import decode_header
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger

class ImapClient:
    """Клиент для работы с IMAP-сервером"""

    def __init__(self, server: str, port: int, email_address: str, password: str):
        """
        Инициализация IMAP клиента

        Args:
            server: адрес IMAP сервера
            port: порт IMAP сервера
            email_address: адрес электронной почты
            password: пароль от почты
        """
        self.server = server
        self.port = port
        self.email_address = email_address
        self.password = password
        self.imap = None

    def connect(self) -> bool:
        """
        Установка соединения с IMAP сервером

        Returns:
            bool: True если соединение успешно, иначе False
        """
        try:
            self.imap = imaplib.IMAP4_SSL(self.server, self.port)
            self.imap.login(self.email_address, self.password)
            logger.success(f"Успешно подключились к {self.server} как {self.email_address}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к IMAP серверу: {e}")
            return False


    def disconnect(self) -> None:
        """Закрытие соединения с IMAP сервером"""
        if self.imap:
            try:
                # Проверяем, активно ли соединение, перед его закрытием
                # Пробуем выполнить простую команду noop
                try:
                    status, _ = self.imap.noop()
                    if status == 'OK':
                        # Соединение активно, можно закрывать
                        self.imap.logout()
                        logger.info("Соединение с IMAP сервером закрыто")
                    else:
                        logger.info("Соединение с IMAP сервером уже было закрыто")
                except Exception:
                    # Если команда вызвала ошибку, значит соединение уже не активно
                    logger.info("Соединение с IMAP сервером уже не активно")
                    # Устанавливаем imap в None, чтобы избежать повторных попыток закрытия
                    self.imap = None
            except Exception as e:
                logger.error(f"Ошибка при закрытии соединения: {e}")
                # Устанавливаем imap в None, чтобы избежать повторных попыток закрытия
                self.imap = None


    def select_mailbox(self, mailbox: str = 'INBOX') -> bool:
        """
        Выбор почтового ящика (папки) для дальнейшей работы

        Args:
            mailbox: название почтового ящика, по умолчанию 'INBOX'

        Returns:
            bool: True если выбор успешен, иначе False
        """
        if not self.imap:
            logger.error("Нет соединения с IMAP сервером")
            return False

        try:
            response, data = self.imap.select(mailbox)
            if response != 'OK' or not data[0]:
                logger.error(f"Не удалось выбрать папку {mailbox}: {response}")
                return False
            logger.info(f"Выбрана папка {mailbox}, {data[0].decode()} писем")
            return True
        except Exception as e:
            logger.error(f"Ошибка при выборе папки {mailbox}: {e}")
            return False

    def get_unseen_emails_ids(self) -> List[str]:
        """
        Получение ID непрочитанных писем в текущей папке

        Returns:
            List[str]: список ID непрочитанных писем
        """
        if not self.imap:
            logger.error("Нет соединения с IMAP сервером")
            return []

        try:
            response, data = self.imap.search(None, 'UNSEEN')
            if response != 'OK':
                logger.error(f"Не удалось найти непрочитанные письма: {response}")
                return []

            # Разбиваем байтовую строку на ID писем
            email_ids = data[0].split()
            logger.info(f"Найдено {len(email_ids)} непрочитанных писем")
            return [id.decode() for id in email_ids]
        except Exception as e:
            logger.error(f"Ошибка при поиске непрочитанных писем: {e}")
            return []

    def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение письма по его ID

        Args:
            email_id: ID письма

        Returns:
            Optional[Dict[str, Any]]: словарь с данными письма или None в случае ошибки
        """
        if not self.imap:
            logger.error("Нет соединения с IMAP сервером")
            return None

        try:
            response, msg_data = self.imap.fetch(email_id, '(RFC822)')
            if response != 'OK' or not msg_data[0]:
                logger.error(f"Не удалось получить письмо с ID {email_id}: {response}")
                return None

            # Парсим письмо
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email) # type: ignore

            # Декодируем тему
            subject = self._decode_header(msg.get('Subject', ''))

            # Получаем отправителя
            from_addr = self._decode_header(msg.get('From', ''))

            # Получаем тело письма (текст и HTML)
            text_body, html_body = self._get_email_body(msg)

            logger.info(f"Получено письмо: {subject} от {from_addr}")

            return {
                'id': email_id,
                'subject': subject,
                'from': from_addr,
                'text_body': text_body,
                'html_body': html_body,
                'raw_message': msg
            }
        except Exception as e:
            logger.error(f"Ошибка при получении письма с ID {email_id}: {e}")
            return None

    def _decode_header(self, header: str) -> str:
        """
        Декодирование заголовка письма

        Args:
            header: закодированный заголовок

        Returns:
            str: декодированный заголовок
        """
        if not header:
            return ""

        try:
            decoded_parts = decode_header(header)
            result = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        part = part.decode(encoding)
                    else:
                        part = part.decode('utf-8', errors='replace')
                result += str(part)

            return result
        except Exception as e:
            logger.error(f"Ошибка декодирования заголовка: {e}")
            return header

    def _get_email_body(self, msg) -> Tuple[str, str]:
        """
        Извлечение текстового и HTML тела письма

        Args:
            msg: объект письма

        Returns:
            Tuple[str, str]: (текстовое тело, HTML тело)
        """
        text_body = ""
        html_body = ""

        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    # Пропускаем вложения
                    if "attachment" in content_disposition:
                        continue

                    if content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            text_body = body
                        except Exception as e:
                            logger.error(f"Ошибка декодирования текстового тела: {e}")

                    elif content_type == "text/html":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                            html_body = body
                        except Exception as e:
                            logger.error(f"Ошибка декодирования HTML тела: {e}")
            else:
                content_type = msg.get_content_type()
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                    if content_type == "text/plain":
                        text_body = body
                    elif content_type == "text/html":
                        html_body = body
                except Exception as e:
                    logger.error(f"Ошибка декодирования тела: {e}")
        except Exception as e:
            logger.error(f"Ошибка при получении тела письма: {e}")

        return text_body, html_body

    def mark_as_read(self, email_id: str) -> bool:
        """
        Пометить письмо как прочитанное

        Args:
            email_id: ID письма

        Returns:
            bool: True если успешно, иначе False
        """
        if not self.imap:
            logger.error("Нет соединения с IMAP сервером")
            return False

        try:
            self.imap.store(email_id, '+FLAGS', '\\Seen')
            logger.info(f"Письмо {email_id} помечено как прочитанное")
            return True
        except Exception as e:
            logger.error(f"Ошибка при пометке письма как прочитанное: {e}")
            return False