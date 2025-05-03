from loguru import logger
from config import settings
from services.email_manager import EmailManager


def main():
    """Основная функция приложения"""
    logger.info("Запуск приложения для обработки почты")

    # Создаем менеджер для обработки почты
    manager = EmailManager(settings)

    try:
        # Запускаем менеджер в бесконечном цикле
        manager.start()
    except KeyboardInterrupt:
        logger.info("Работа скрипта остановлена пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
    finally:
        # В случае ошибки убеждаемся, что все соединения закрыты
        manager.stop()
        logger.info("Работа приложения завершена")

if __name__ == "__main__":
    main()