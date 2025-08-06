"""
API Gateway Service - единая точка входа для всех запросов
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

import redis
import httpx
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.domain.entities.request import Request
from src.infrastructure.persistence.in_memory_repositories import InMemoryRequestRepository
from src.application.commands.request_commands import (
    CreateRequestCommand,
    CreateRequestCommandHandler
)
from src.application.commands.command_bus import CommandBus
from src.shared.utils.logger import logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logger

app = FastAPI(title="RAG API Gateway", version="2.0.0")

# Подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Глобальные переменные
request_repository: Optional[InMemoryRequestRepository] = None
command_bus: Optional[CommandBus] = None

class CheckRequest(BaseModel):
    """Запрос на проверку текста"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class CheckResponse(BaseModel):
    """Ответ на проверку"""
    success: bool
    result: str
    processing_time: float
    timestamp: str
    confidence: float = 0.0
    extremist_reason: str = ""
    court_date: str = ""
    court_name: str = ""
    material_name: str = ""
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Ответ проверки здоровья"""
    status: str
    service: str
    timestamp: str
    dependencies: Dict[str, str]

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global request_repository, command_bus
    
    try:
        logger.info("🚀 Инициализация API Gateway...")
        
        # Инициализируем репозиторий запросов
        request_repository = InMemoryRequestRepository()
        
        # Инициализируем шину команд
        command_bus = CommandBus()
        
        # Регистрируем обработчики команд
        command_bus.register_handler(
            CreateRequestCommand,
            CreateRequestCommandHandler(request_repository)
        )
        
        logger.info("✅ API Gateway готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации API Gateway: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем Redis
        redis_healthy = "healthy"
        try:
            redis_client.ping()
        except:
            redis_healthy = "unhealthy"
        
        # Проверяем другие сервисы
        services_healthy = "healthy"
        try:
            # Здесь можно добавить проверки других сервисов
            pass
        except:
            services_healthy = "unhealthy"
        
        return HealthResponse(
            status="healthy",
            service="api-gateway",
            timestamp=datetime.now().isoformat(),
            dependencies={
                "redis": redis_healthy,
                "services": services_healthy
            }
        )
    except Exception as e:
        logger.error(f"❌ Ошибка health check: {e}")
        return HealthResponse(
            status="unhealthy",
            service="api-gateway",
            timestamp=datetime.now().isoformat(),
            dependencies={
                "redis": "unknown",
                "services": "unknown"
            }
        )

@app.post("/check", response_model=CheckResponse)
async def check_text(request: CheckRequest):
    """Проверка текста на экстремизм"""
    start_time = time.time()
    
    try:
        # Приводим запрос к нижнему регистру для единообразия
        query_lower = request.query.lower()
        logger.info(f"📝 Получен запрос на проверку: {query_lower[:50]}...")
        
        # Создаем команду
        command = CreateRequestCommand(
            query=query_lower,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Обрабатываем команду
        result = await command_bus.handle(command)
        
        processing_time = time.time() - start_time
        
        # Отправляем запрос в Request Processor для координации сервисов
        async with httpx.AsyncClient() as client:
            try:
                # Запрос к Request Processor
                request_data = {
                    "query": query_lower,
                    "user_id": request.user_id
                }
                logger.info(f"🔍 Отправка запроса в request-processor: data={request_data}")
                processor_response = await client.post(
                    "http://request-processor:8004/check-text",
                    json=request_data,
                    timeout=15.0
                )
                
                if processor_response.status_code == 200:
                    processor_data = processor_response.json()
                    logger.info(f"📊 Ответ от request-processor: {processor_data}")
                    
                    # Анализируем результаты
                    is_extremist = processor_data.get("is_extremist", False)
                    confidence = processor_data.get("confidence", 0.0)
                    matches = processor_data.get("matches", [])
                    logger.info(f"🎯 Результат анализа: is_extremist={is_extremist}, confidence={confidence}")
                    
                    if is_extremist:
                        return CheckResponse(
                            success=True,
                            result="Обнаружены признаки экстремизма",
                            processing_time=processing_time,
                            timestamp=datetime.now().isoformat(),
                            confidence=confidence,
                            extremist_reason=processor_data.get("reason", "Найдены совпадения в базе данных"),
                            court_date=processor_data.get("court_date", ""),
                            court_name="Министерство юстиции РФ",
                            material_name=processor_data.get("material_name", "")
                        )
                    else:
                        return CheckResponse(
                            success=True,
                            result="Признаки экстремизма не обнаружены",
                            processing_time=processing_time,
                            timestamp=datetime.now().isoformat(),
                            confidence=confidence,
                            extremist_reason="Не обнаружено признаков экстремизма",
                            court_date="",
                            court_name="",
                            material_name=""
                        )
                else:
                    # Request Processor недоступен - возвращаем ошибку
                    return CheckResponse(
                        success=False,
                        result="",
                        processing_time=processing_time,
                        timestamp=datetime.now().isoformat(),
                        error="Request Processor недоступен"
                    )
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при обращении к Request Processor: {e}")
                # Возвращаем ошибку вместо fallback
                return CheckResponse(
                    success=False,
                    result="",
                    processing_time=processing_time,
                    timestamp=datetime.now().isoformat(),
                    error=f"Ошибка Request Processor: {str(e)}"
                )
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке текста: {e}")
        processing_time = time.time() - start_time
        
        return CheckResponse(
            success=False,
            result="",
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@app.get("/statistics")
async def get_statistics():
    """Получение статистики"""
    try:
        if request_repository is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        stats = request_repository.get_statistics()
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Ошибка при получении статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 