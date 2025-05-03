# tests/conftest.py
import time
from services.gemini_client import GeminiClient
from config import settings
import pytest




@pytest.fixture
def gemini_client():
    client = GeminiClient(settings.gemini.api_key, debug=True)
    return client


@pytest.fixture()
def throttle():
    """Фикстура для ограничения частоты вызова API (8 сек между тестами)"""
    yield  # Выполняется тест
    time.sleep(5)