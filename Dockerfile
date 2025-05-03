FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только файл requirements.txt сначала
# Это позволит использовать кэширование слоев Docker
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Создаем пользователя без прав администратора для запуска приложения
RUN useradd -m appuser
USER appuser

# Запускаем приложение
CMD ["python", "main.py"]