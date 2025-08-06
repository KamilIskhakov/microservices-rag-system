"""
Request Processor Service - координация запросов между сервисами
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

import redis
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.domain.entities.request import Request
from src.infrastructure.persistence.in_memory_repositories import InMemoryRequestRepository as RequestRepository
from src.application.commands.request_commands import (
    ProcessRequestCommand,
    ProcessRequestCommandHandler,
    CommandBus
)
from src.shared.utils.logger import logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logger

app = FastAPI(title="RAG Request Processor Service", version="2.0.0")

# Подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Глобальные переменные
request_repository: Optional[RequestRepository] = None
command_bus: Optional[CommandBus] = None

# Импортируем конфигурацию
from src.shared.config.config_manager import ConfigManager

# Инициализируем конфигурацию
config_manager = ConfigManager()

# Конфигурация сервисов из переменных окружения
SERVICES = {
    "ai-model": config_manager.get_service_url("ai_model"),
    "vectorstore": config_manager.get_service_url("vectorstore"),
    "scraper": config_manager.get_service_url("scraper"),
    "payment": config_manager.get_service_url("payment")
}

class ProcessRequest(BaseModel):
    """Запрос на обработку"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    services: List[str] = ["ai-model", "vectorstore"]  # Какие сервисы использовать

class ProcessResponse(BaseModel):
    """Ответ на обработку"""
    success: bool
    request_id: Optional[str] = None
    results: Dict[str, Any] = {}
    processing_time: float = 0.0
    timestamp: str
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
        logger.info("🚀 Инициализация Request Processor Service...")
        
        # Инициализируем репозиторий запросов
        request_repository = RequestRepository()
        
        # Инициализируем шину команд
        command_bus = CommandBus()
        
        # Регистрируем обработчики команд
        command_bus.register_handler(
            ProcessRequestCommand,
            ProcessRequestCommandHandler(request_repository)
        )
        
        logger.info("✅ Request Processor Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Request Processor Service: {e}")
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
        
        # Проверяем доступность других сервисов
        dependencies = {
            "redis": redis_healthy,
            "ai-model": "unknown",
            "vectorstore": "unknown",
            "scraper": "unknown",
            "payment": "unknown"
        }
        
        # Проверяем каждый сервис
        async with httpx.AsyncClient() as client:
            for service_name, service_url in SERVICES.items():
                try:
                    response = await client.get(f"{service_url}/health", timeout=5.0)
                    if response.status_code == 200:
                        dependencies[service_name] = "healthy"
                    else:
                        dependencies[service_name] = "unhealthy"
                except:
                    dependencies[service_name] = "unhealthy"
        
        overall_status = "healthy" if all(
            status == "healthy" for status in dependencies.values()
        ) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            service="request-processor",
            timestamp=datetime.now().isoformat(),
            dependencies=dependencies
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="request-processor",
            timestamp=datetime.now().isoformat(),
            dependencies={"error": str(e)}
        )

@app.post("/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """Обработка запроса через координацию сервисов"""
    start_time = time.time()
    
    try:
        logger.info(f"🔄 Обработка запроса: {request.query[:50]}...")
        
        # Создаем команду для обработки запроса
        command = ProcessRequestCommand(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            services=request.services
        )
        
        # Отправляем команду через шину команд
        result = await command_bus.handle(command)
        
        processing_time = time.time() - start_time
        
        return ProcessResponse(
            success=True,
            request_id=result.request_id,
            results=result.results,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки запроса: {e}")
        processing_time = time.time() - start_time
        
        return ProcessResponse(
            success=False,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

class CheckTextRequest(BaseModel):
    """Запрос на проверку текста"""
    query: str
    user_id: Optional[str] = None

@app.post("/check-text")
async def check_text(request: CheckTextRequest):
    # Приводим запрос к нижнему регистру для единообразия
    query = request.query.lower()
    user_id = request.user_id
    logger.info(f"🔍 Получен запрос: query='{query}', user_id='{user_id}'")
    """Проверка текста на экстремизм через координацию сервисов"""
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Проверка текста: {query[:50]}...")
        
        results = {}
        
        # 1. Поиск в Vector Store Service
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"🔍 Отправка запроса в Vector Store Service: query='{query}'")
                vector_response = await client.post(
                    f"{SERVICES['vectorstore']}/search",
                    json={"query": query, "top_k": 5, "threshold": 0.3},
                    timeout=5.0
                )
                
                if vector_response.status_code == 200:
                    vector_data = vector_response.json()
                    results["vectorstore"] = vector_data
                else:
                    results["vectorstore"] = {"error": "Vector Store Service unavailable"}
                    
            except Exception as e:
                results["vectorstore"] = {"error": str(e)}
        
        # 2. Генерация ответа через AI модель
        async with httpx.AsyncClient() as client:
            try:
                # Выбираем наиболее релевантный документ из результатов поиска
                vector_results = results.get("vectorstore", {}).get("results", [])
                context_text = ""
                selected_document = None
                
                if vector_results:
                    # Выбираем наиболее релевантный документ, исключая "исключен"
                    selected_document = None
                    for doc in vector_results:
                        if "исключен" not in doc['text'].lower() and "материал исключен" not in doc['text'].lower():
                            selected_document = doc
                            break
                    
                    # Если не нашли подходящий, берем первый
                    if not selected_document:
                        selected_document = vector_results[0]
                    
                    context_text = f"- {selected_document['text']}"
                    logger.info(f"🎯 Выбран документ для AI анализа: {selected_document['text'][:100]}...")
                
                # Создаем короткий промпт для быстрого анализа
                ai_prompt = f"""Запрос: "{query}"
Материал: {context_text}

Есть ли СМЫСЛОВАЯ связь? (не просто совпадение слов)

Ответ: Да/Нет - [объяснение]"""

                ai_response = await client.post(
                    f"{SERVICES['ai-model']}/generate",
                    json={
                        "query": ai_prompt,
                        "context": [],
                        "max_length": config_manager.get_max_new_tokens(),
                        "temperature": config_manager.get_generation_temperature()
                    },
                    timeout=config_manager.get_max_generation_time()
                )
                
                if ai_response.status_code == 200:
                    ai_data = ai_response.json()
                    results["ai-model"] = ai_data
                else:
                    results["ai-model"] = {"error": "AI model unavailable"}
                    
            except Exception as e:
                results["ai-model"] = {"error": str(e)}
        
        # 3. Формирование финального ответа
        final_result = {
            "query": query,
            "is_extremist": False,
            "confidence": 0.0,
            "reason": "Не удалось определить",
            "sources": []
        }
        
        # Анализируем результаты векторного поиска и AI анализа
        logger.info(f"🔍 Анализ результатов vectorstore: {results.get('vectorstore', {})}")
        logger.info(f"🤖 Анализ результатов AI: {results.get('ai-model', {})}")
        
        vector_results = results.get("vectorstore", {}).get("results", [])
        ai_result = results.get("ai-model", {})
        
        logger.info(f"📊 Найдено результатов: {len(vector_results)}")
        
        if vector_results and selected_document:
            best_match = selected_document
            logger.info(f"🎯 Выбранный документ: relevance_score={best_match.get('relevance_score')}, text={best_match.get('text', '')[:100]}...")
            
            # Используем AI анализ для определения смысловой связи
            if "result" in ai_result and ai_result.get("success", False):
                ai_response = ai_result["result"].lower()
                logger.info(f"🤖 AI анализ: {ai_response}")
                
                # Анализируем ответ AI модели
                ai_response_lower = ai_response.lower()
                
                # Проверяем на "Да" в начале ответа
                if ai_response_lower.startswith("да"):
                    final_result["is_extremist"] = True
                    final_result["confidence"] = 0.9  # Высокая уверенность при подтверждении AI
                    final_result["reason"] = f"AI анализ подтвердил связь с экстремистским материалом: {ai_response}"
                elif ai_response_lower.startswith("нет"):
                    final_result["is_extremist"] = False
                    final_result["confidence"] = 0.8
                    final_result["reason"] = f"AI анализ не выявил связи с экстремистскими материалами: {ai_response}"
                else:
                    # Если AI не дал четкого ответа, используем векторный поиск
                    final_result["is_extremist"] = True
                    final_result["confidence"] = 1.0 - best_match["relevance_score"]
                    final_result["reason"] = f"Найден в реестре экстремистских материалов"
            else:
                # Если AI недоступен, используем только векторный поиск
                final_result["is_extremist"] = True
                final_result["confidence"] = 1.0 - best_match["relevance_score"]
                final_result["reason"] = f"Найден в реестре экстремистских материалов"
            
            # Извлекаем информацию о материале
            if "metadata" in best_match:
                metadata = best_match["metadata"]
                final_result["material_name"] = metadata.get("content", "")
                final_result["material_number"] = metadata.get("number", "")
                final_result["court_date"] = metadata.get("date", "")
            
            final_result["sources"] = [best_match]  # Только выбранный документ
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "is_extremist": final_result["is_extremist"],
            "confidence": final_result["confidence"],
            "reason": final_result["reason"],
            "matches": final_result["sources"],
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "services_used": list(results.keys()),
            "material_name": final_result.get("material_name", ""),
            "material_number": final_result.get("material_number", ""),
            "court_date": final_result.get("court_date", "")
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки текста: {e}")
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "is_extremist": False,
            "confidence": 0.0,
            "reason": f"Ошибка обработки: {str(e)}",
            "matches": [],
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/requests/{request_id}")
async def get_request(request_id: str):
    """Получение информации о запросе"""
    try:
        request = request_repository.get_request(request_id)
        
        if request is None:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return {
            "success": True,
            "request": {
                "id": request.id,
                "query": request.query,
                "user_id": request.user_id,
                "status": request.status,
                "created_at": request.created_at.isoformat(),
                "completed_at": request.completed_at.isoformat() if request.completed_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request {request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/requests/user/{user_id}")
async def get_user_requests(user_id: str, limit: int = 10):
    """Получение запросов пользователя"""
    try:
        requests = request_repository.get_user_requests(user_id, limit)
        
        return {
            "success": True,
            "requests": [
                {
                    "id": req.id,
                    "query": req.query,
                    "status": req.status,
                    "created_at": req.created_at.isoformat()
                }
                for req in requests
            ],
            "count": len(requests)
        }
        
    except Exception as e:
        logger.error(f"Error getting requests for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Получение статистики обработки запросов"""
    try:
        stats = request_repository.get_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/services/{service_name}/health")
async def check_service_health(service_name: str):
    """Проверка здоровья конкретного сервиса"""
    try:
        if service_name not in SERVICES:
            raise HTTPException(status_code=404, detail="Service not found")
        
        service_url = SERVICES[service_name]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{service_url}/health", timeout=5.0)
            
            return {
                "success": True,
                "service": service_name,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response": response.json() if response.status_code == 200 else None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error checking health for service {service_name}: {e}")
        return {
            "success": False,
            "service": service_name,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 