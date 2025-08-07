#!/bin/bash

# Скрипт для запуска чистых микросервисов
# Каждый сервис полностью независим со своей доменной логикой

set -e

echo "🚀 Запуск чистых микросервисов..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "📝 Создаем .env файл из примера..."
    cp env.example .env
fi

# Проверяем наличие моделей
if [ ! -d "models/qwen-model_full" ]; then
    echo "⚠️  Внимание: Модели не найдены в models/qwen-model_full"
    echo "   Скачайте модели или используйте заглушки"
fi

# Останавливаем существующие контейнеры
echo "🛑 Останавливаем существующие контейнеры..."
docker-compose -f infrastructure/docker/docker-compose.optimized.yml down

# Удаляем старые образы (опционально)
if [ "$1" = "--clean" ]; then
    echo "🧹 Удаляем старые образы..."
    docker-compose -f infrastructure/docker/docker-compose.optimized.yml down --rmi all
fi

# Собираем и запускаем контейнеры
echo "🔨 Собираем и запускаем контейнеры..."
docker-compose -f infrastructure/docker/docker-compose.optimized.yml up --build -d

# Ждем запуска сервисов
echo "⏳ Ждем запуска сервисов..."
sleep 30

# Проверяем здоровье сервисов
echo "🏥 Проверяем здоровье сервисов..."

# Redis
echo "📊 Redis:"
curl -f http://localhost:6379 || echo "❌ Redis недоступен"

# AI Model Service
echo "🤖 AI Model Service:"
curl -f http://localhost:8003/health || echo "❌ AI Model Service недоступен"

# Vector Store Service
echo "📚 Vector Store Service:"
curl -f http://localhost:8002/health || echo "❌ Vector Store Service недоступен"

# Scraper Service
echo "🕷️  Scraper Service:"
curl -f http://localhost:8001/health || echo "❌ Scraper Service недоступен"

# Request Processor Service
echo "⚙️  Request Processor Service:"
curl -f http://localhost:8004/health || echo "❌ Request Processor Service недоступен"

# Payment Service
echo "💳 Payment Service:"
curl -f http://localhost:8005/health || echo "❌ Payment Service недоступен"

# API Gateway
echo "🌐 API Gateway:"
curl -f http://localhost:8000/health || echo "❌ API Gateway недоступен"

echo ""
echo "✅ Все сервисы запущены!"
echo ""
echo "📋 Доступные сервисы:"
echo "   - API Gateway: http://localhost:8000"
echo "   - AI Model Service: http://localhost:8003"
echo "   - Vector Store Service: http://localhost:8002"
echo "   - Scraper Service: http://localhost:8001"
echo "   - Request Processor Service: http://localhost:8004"
echo "   - Payment Service: http://localhost:8005"
echo "   - Redis: localhost:6379"
echo ""
echo "🔍 Логи контейнеров:"
echo "   docker-compose -f infrastructure/docker/docker-compose.optimized.yml logs -f"
echo ""
echo "🛑 Остановка сервисов:"
echo "   docker-compose -f infrastructure/docker/docker-compose.optimized.yml down"
