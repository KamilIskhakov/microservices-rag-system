FROM python:3.10-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения (но не модели)
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/data /app/models

# Устанавливаем переменные окружения для CPU
ENV CUDA_VISIBLE_DEVICES=""
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]