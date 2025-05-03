import json

from services.gemini_client import GeminiClient
import pytest
from typing import TypedDict

class LetterData(TypedDict):
    classification: str
    subject: str
    body: str


def load_test_data() -> LetterData:
    with open("tests/src/letters.json") as fp:
        return json.load(fp)

# Параметризованный тест для классификации каждого письма
@pytest.mark.parametrize("letter_data", load_test_data())
def test_classification(letter_data: LetterData, gemini_client: GeminiClient, throttle):
    print(f"\n\n{"*"*15} {letter_data["subject"]} {"*"*15}")
    subject = letter_data.get("subject", "")
    body = letter_data.get("body", "")
    expected_category = letter_data.get("classification", "other")
    result_category = gemini_client.classify_email(subject, body)
    # time.sleep(8)
    assert result_category.value in expected_category, \
        f"{subject}\nНесоответствие категорий: ожидалось {expected_category}, получено {result_category.value}"