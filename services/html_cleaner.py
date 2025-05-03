"""
Утилита для очистки HTML из текста электронных писем
"""
import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from loguru import logger


class EmailCleaner:
    """Класс для очистки данных электронных писем от HTML и форматирования"""

    @staticmethod
    def clean_email_data(email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Очищает данные электронного письма

        Args:
            email_data: Исходные данные письма из IMAP клиента

        Returns:
            Очищенные данные письма
        """
        cleaned_data = email_data.copy()

        # Очищаем HTML тело письма, если оно есть
        if cleaned_data.get('html_body'):
            cleaned_data['text_content'] = EmailCleaner.html_to_text(cleaned_data['html_body'])
        else:
            # Используем текстовое представление, если оно есть
            cleaned_data['text_content'] = cleaned_data.get('text_body', '')

        # Очищаем тему от лишних пробелов и переносов строк
        if cleaned_data.get('subject'):
            cleaned_data['subject'] = EmailCleaner.clean_text(cleaned_data['subject'])

        # Извлекаем имя отправителя из email-адреса
        if cleaned_data.get('from'):
            cleaned_data['sender_name'] = EmailCleaner.extract_sender_name(cleaned_data['from'])

        # Добавляем другие поля по необходимости

        return cleaned_data

    @staticmethod
    def html_to_text(html_content: str) -> str:
        """
        Преобразует HTML-контент в обычный текст

        Args:
            html_content: HTML-контент письма

        Returns:
            Текстовое представление без HTML-тегов
        """
        try:
            # Используем BeautifulSoup для извлечения текста из HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Удаляем скрипты и стили
            for script_or_style in soup(['script', 'style']):
                script_or_style.decompose()

            # Получаем текст
            text = soup.get_text(separator=' ', strip=True)

            # Очищаем текст
            return EmailCleaner.clean_text(text)

        except Exception as e:
            logger.error(f"Ошибка при очистке HTML: {e}")
            # Возвращаем пустую строку в случае ошибки
            return ""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Очищает текст от лишних пробелов, переносов строк и т.д.

        Args:
            text: Исходный текст

        Returns:
            Очищенный текст
        """
        if not text:
            return ""

        # Заменяем множественные пробелы и переносы строк на один пробел
        text = re.sub(r'\s+', ' ', text)

        # Удаляем лишние пробелы в начале и конце
        text = text.strip()

        # Удаляем специальные символы HTML
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)

        return text

    @staticmethod
    def extract_sender_name(from_field: str) -> str:
        """
        Извлекает имя отправителя из поля 'From'

        Args:
            from_field: Строка с информацией об отправителе

        Returns:
            Имя отправителя
        """
        try:
            # Если формат "Name <email@example.com>"
            match = re.search(r'([^<]+)<', from_field)
            if match:
                return EmailCleaner.clean_text(match.group(1))

            # Если просто email
            return from_field.split('@')[0]

        except Exception as e:
            logger.error(f"Ошибка при извлечении имени отправителя: {e}")
            return from_field