from loguru import logger
from config import settings
from services import EmailManager, TelegramBot

def main():
    """Основная функция приложения"""
    logger.info("Запуск приложения для обработки почты с Yandex & Google")

    # Создаем менеджер для обработки почты
    manager = EmailManager(settings)

    # Создаем объект Telegram бота для отправки уведомлений об ошибках
    tg_bot = TelegramBot(token=settings.bot.token, client_id=settings.bot.client_id)
    tg_bot.start()
    tg_bot.send_hello_message("Запустился парсер почты")

    try:
        # Запускаем менеджер в бесконечном цикле
        manager.start()
    except KeyboardInterrupt:
        logger.info("Работа скрипта остановлена пользователем")
    except Exception as e:
        error_msg = f"Критическая ошибка: {str(e)}"
        logger.exception(error_msg)

        # Отправляем уведомление об ошибке через Telegram
        tg_bot.send_error_message(error_msg)
    finally:
        # В случае ошибки убеждаемся, что все соединения закрыты
        manager.stop()
        logger.info("Работа приложения завершена")

if __name__ == "__main__":
    main()