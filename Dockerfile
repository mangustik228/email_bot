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

# Пользователь задаётся в рантайме через docker-compose (user: APP_UID:APP_GID),
# чтобы владелец bind-mount'ов на хосте совпадал с UID процесса в контейнере.

# Запускаем приложение
CMD ["python", "main.py"]