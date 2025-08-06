#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Запуск оптимизированного RAG Chrome Extension...${NC}"

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker не установлен. Установите Docker и попробуйте снова.${NC}"
    exit 1
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова.${NC}"
    exit 1
fi

# Проверка наличия модели
if [ ! -d "models/qwen-model_full" ]; then
    echo -e "${YELLOW}⚠️  Модель qwen-model_full не найдена в models/qwen-model_full/${NC}"
    echo -e "${YELLOW}   Пожалуйста, загрузите модель в папку models/qwen-model_full/${NC}"
    echo -e "${YELLOW}   Для тестирования можно создать пустую папку: mkdir -p models/qwen-model_full${NC}"
    read -p "Создать пустую папку для модели? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p models/qwen-model_full
        echo -e "${GREEN}✅ Создана папка models/qwen-model_full${NC}"
    else
        echo -e "${RED}❌ Модель необходима для работы. Выход.${NC}"
        exit 1
    fi
fi

# Остановка существующих контейнеров
echo -e "${YELLOW}🛑 Остановка существующих контейнеров...${NC}"
docker-compose -f infrastructure/docker/docker-compose.optimized.yml down

# Удаление старых образов (опционально)
read -p "Удалить старые образы Docker? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🗑️  Удаление старых образов...${NC}"
    docker system prune -f
fi

# Сборка и запуск контейнеров
echo -e "${BLUE}🔨 Сборка и запуск контейнеров...${NC}"
docker-compose -f infrastructure/docker/docker-compose.optimized.yml up --build -d

# Ожидание запуска сервисов
echo -e "${YELLOW}⏳ Ожидание запуска сервисов...${NC}"
sleep 30

# Проверка статуса сервисов
echo -e "${BLUE}🔍 Проверка статуса сервисов...${NC}"

# Redis
if curl -f http://localhost:6379 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis запущен на порту 6379${NC}"
else
    echo -e "${RED}❌ Redis не отвечает на порту 6379${NC}"
fi

# API Gateway
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API Gateway запущен на порту 8000${NC}"
else
    echo -e "${YELLOW}⏳ API Gateway еще запускается на порту 8000${NC}"
fi

# AI Model Service
if curl -f http://localhost:8003/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ AI Model Service запущен на порту 8003${NC}"
else
    echo -e "${YELLOW}⏳ AI Model Service еще запускается на порту 8003${NC}"
fi

# Vector Store Service
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Vector Store Service запущен на порту 8002${NC}"
else
    echo -e "${YELLOW}⏳ Vector Store Service еще запускается на порту 8002${NC}"
fi

# Scraper Service
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Scraper Service запущен на порту 8001${NC}"
else
    echo -e "${YELLOW}⏳ Scraper Service еще запускается на порту 8001${NC}"
fi

# Payment Service
if curl -f http://localhost:8005/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Payment Service запущен на порту 8005${NC}"
else
    echo -e "${YELLOW}⏳ Payment Service еще запускается на порту 8005${NC}"
fi

# Request Processor Service
if curl -f http://localhost:8004/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Request Processor Service запущен на порту 8004${NC}"
else
    echo -e "${YELLOW}⏳ Request Processor Service еще запускается на порту 8004${NC}"
fi

echo -e "${GREEN}🎉 Проект запущен оптимизированно!${NC}"
echo -e "${BLUE}📋 Доступные сервисы:${NC}"
echo -e "   🌐 API Gateway: http://localhost:8000"
echo -e "   🤖 AI Model: http://localhost:8003"
echo -e "   🗄️  Vector Store: http://localhost:8002"
echo -e "   📡 Scraper: http://localhost:8001"
echo -e "   💳 Payment: http://localhost:8005"
echo -e "   ⚙️  Request Processor: http://localhost:8004"
echo -e "   🔴 Redis: localhost:6379"

echo -e "${BLUE}📚 Документация API:${NC}"
echo -e "   📖 Swagger UI: http://localhost:8000/docs"
echo -e "   📖 ReDoc: http://localhost:8000/redoc"

echo -e "${YELLOW}🧪 Тестирование:${NC}"
echo -e "   curl -X POST http://localhost:8000/check \\"
echo -e "     -H \"Content-Type: application/json\" \\"
echo -e "     -d '{\"query\": \"текст для проверки\", \"user_id\": \"user123\"}'"

echo -e "${YELLOW}🛑 Для остановки: docker-compose -f infrastructure/docker/docker-compose.optimized.yml down${NC}" 