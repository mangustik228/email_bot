from enum import Enum


class EmailCategory(Enum):
    """Категории электронных писем"""
    ALERT = "alert"              # Срочные
    PAYMENT = "payment"          # Транзакционные письма (покупки, выписки)
    MESSAGE = "message"          # Личные письма и по работе
    SUPPORT = "support"          # Ответы от тех поддержек
    NOTICE = "notice"            # Простые уведомления, рассылки, новостные письма
    OTHER = "other"              # Другое
    IMPORTANT = "important"      # Уведомления, которые не хочет выносить в notice