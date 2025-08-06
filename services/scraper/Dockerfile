FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY services/scraper/requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY services/scraper/ .
COPY src/ ./src/

# Создание пользователя для безопасности
RUN useradd -m -u 1000 appuser

# Создание директории data и установка прав
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

# Открытие порта
EXPOSE 8001

# Запуск приложения
CMD ["uvicorn", "scraper_service:app", "--host", "0.0.0.0", "--port", "8001"] 