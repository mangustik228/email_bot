"""
Клиент для взаимодействия с Google Gemini API
для классификации электронных писем
"""
import json
import time
from typing import Optional

from google import genai
from loguru import logger

from schemas import EmailCategory
from .prompt_classification import PROMT_CLASSIFICATION

class GeminiClient:
    """Клиент для работы с Google Gemini API"""

    # Модель для классификации
    # MODEL = "gemini-2.0-flash"
    MODEL = "gemini-2.5-flash-preview-04-17"

    def __init__(self, api_key: str, debug: bool):
        """
        Инициализация клиента Google Gemini

        Args:
            api_key: API ключ Google Gemini
        """
        self.api_key = api_key
        # Инициализация Google Gemini клиента
        self.client = genai.Client(api_key=api_key)
        self.debug = debug
        logger.info("GeminiClient инициализирован")

    def classify_email(self, subject: str, body: str) -> EmailCategory:
        """
        Классифицирует электронное письмо по категориям

        Args:
            subject: Тема письма
            body: Текст письма (очищенный от HTML)

        Returns:
            Категория письма из EmailCategory
        """
        try:
            logger.info(f"Начинаю классифицировать: {subject}")
            # Формируем запрос для классификации
            prompt = self._create_classification_prompt(subject, body)
            # Отправляем запрос к API
            response = self._generate_content(prompt)

            # Обрабатываем ответ
            if not response:
                logger.error("Пустой ответ от Gemini API")
                return EmailCategory.OTHER

            # Извлекаем категорию из ответа
            category = self._extract_category_from_response(response)
            logger.info(f"Письмо классифицировано как: {category}")

            return category

        except Exception as e:
            logger.error(f"Ошибка при классификации письма: {e}")
            return EmailCategory.OTHER


    @property
    def result_format(self):
        if self.debug:
            return """
            Проанализируй тему и содержание письма, затем верни ответ в формате JSON:
            {{
            "category": "ОДНА_ИЗ_КАТЕГОРИЙ",
            "reasoning": "Краткое объяснение, почему письмо отнесено к этой категории"
            }}
            """
        else:
            return "Верни название категории одним словом"

    def _create_classification_prompt(self, subject: str, body: str) -> str:
        """
        Создает промпт для классификации письма
        Args:
            subject: Тема письма
            body: Текст письма
        Returns:
            Подготовленный промпт
        """
        # Ограничиваем размер тела письма для запроса
        truncated_body = body[:1500] if body else ""
        return f"""
    {PROMT_CLASSIFICATION}
    {self.result_format}

    Тема письма: {subject}
    Текст письма:
    {truncated_body}
        """


    def _clean_dirty_json(self, response_text: str) -> dict:
        cleaned_response = response_text.strip()

        # Удаляем маркеры кода в формате ```json ... ```
        if cleaned_response.startswith("```"):
            # Находим конец блока кода
            end_marker = cleaned_response.rfind("```")
            if end_marker > 3:  # Если нашли закрывающий блок
                # Извлекаем только содержимое между маркерами, удаляя ```json\n в начале
                # и ``` в конце
                cleaned_response = cleaned_response[cleaned_response.find("\n", 3)+1:end_marker].strip()
        # Пытаемся распарсить JSON
        response_json = json.loads(cleaned_response)
        return response_json


    def _generate_content(self, prompt: str, is_payment: bool=False) -> Optional[str]:
        """
        Отправляет запрос к API Gemini с помощью официальной библиотеки

        Args:
            prompt: Текст запроса

        Returns:
            Ответ от API или None в случае ошибки
        """
        for _ in range(5):
            try:
                response = self.client.models.generate_content(
                    model=self.MODEL,
                    contents=prompt,
                )
                if is_payment:
                    return response.text
                if not (response_text := response.text if hasattr(response, 'text') else None):
                    return
                if self.debug:
                    response_json = self._clean_dirty_json(response_text)
                    category_str = response_json.get("category", "").lower()
                    reasoning = response_json.get("reasoning", "")
                    # Логируем результат с рассуждением
                    logger.debug(f'Результат классификации: {category_str}')
                    logger.info(f'Причина: {reasoning}')
                    return category_str
                else:
                    return response_text

            except Exception as e:
                logger.warning(f"Ошибка при запросе к Gemini API: {e}")
                time.sleep(3)
        logger.error(f'Не получилось с 5 попыток получить ответ от Gemini')

    def _extract_category_from_response(self, response: str) -> EmailCategory:
        """
        Извлекает категорию из ответа API

        Args:
            response: Текстовый ответ от API Gemini

        Returns:
            Строка с категорией
        """
        if not response:
            return EmailCategory.OTHER

        # Очищаем и нормализуем ответ
        cleaned_text = response.strip().lower()
        try:
            return EmailCategory(cleaned_text)
        except Exception as e:
            logger.warning(f"{e} Не удалось определить категорию из ответа: '{cleaned_text}'")
            return EmailCategory.OTHER


    def extract_payment_data(self, subject: str, body: str) -> dict:
        """
        Извлекает данные о транзакции из письма

        Args:
            subject: Тема письма
            body: Текст письма (очищенный от HTML)

        Returns:
            Словарь с данными о транзакции
        """
        try:
            logger.info(f"Начинаю извлекать данные о транзакции из письма: {subject}")

            # Формируем промпт для извлечения данных
            prompt = self._create_payment_extraction_prompt(subject, body)

            # Отправляем запрос к API
            response = self._generate_content(prompt, is_payment=True)

            logger.debug(f'{response = }')

            if not response:
                logger.error("Пустой ответ от Gemini API при извлечении данных о платеже")
                return {}

            # Извлекаем данные из ответа
            payment_data = self._extract_payment_data_from_response(response)
            logger.info(f"Данные о транзакции извлечены: {payment_data}")

            return payment_data

        except Exception as e:
            logger.error(f"Ошибка при извлечении данных о транзакции: {e}")
            return {}

    def _create_payment_extraction_prompt(self, subject: str, body: str) -> str:
        """
        Создает промпт для извлечения данных о транзакции

        Args:
            subject: Тема письма
            body: Текст письма

        Returns:
            Подготовленный промпт
        """
        # Ограничиваем размер тела письма для запроса
        truncated_body = body[:1500] if body else ""

        return f"""
        Извлеки данные о транзакции из письма и верни их в формате JSON.

        Необходимо извлечь следующие данные:
        - currency: Валюта транзакции (USD, THB, RUB, EUR, BTC и т.д.). Определи по символам $/€/₽/฿/₿ или названию валюты.
        - payment_type: Тип транзакции, платежа из списка: Перевод|P2P покупка|P2P продажа|Подписка|Товар|Иное
        - amount: Итоговая сумма транзакции (число).
        - item: Услуга или товар, за который произведена оплата. (например "Ежемесячная подписка")

        Обязательно верни результат в формате JSON:
        {{
        "currency": "Валюта",
        "payment_type": Перевод/P2P покупка/P2P продажа/Подписка/Товар/Иное
        "amount": число,
        "item": "Название услуги или товара",
        }}

        Если не получается извлечь какие то параметры: поставь null

        Тема письма: {subject}
        Текст письма:
        {truncated_body}
        """

    def _extract_payment_data_from_response(self, response: str) -> dict:
        """
        Извлекает данные о транзакции из ответа API

        Args:
            response: Текстовый ответ от API Gemini

        Returns:
            Словарь с данными о транзакции
        """
        try:
            # Очищаем ответ от возможных маркеров JSON
            cleaned_response = self._clean_dirty_json(response)

            # Добавляем базовую валидацию данных
            if not isinstance(cleaned_response, dict):
                logger.error(f"Неверный формат ответа: {response}")
                return {}

            return cleaned_response
        except Exception as e:
            logger.error(f"Ошибка при извлечении данных о транзакции из ответа: {e}")
            return {}