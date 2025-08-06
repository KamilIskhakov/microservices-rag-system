"""
Request Processor API - координация запросов между сервисами
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
from src.shared.config.config_manager import ConfigManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logger

app = FastAPI(title="RAG Request Processor API", version="2.0.0")

# Инициализируем конфигурацию
config_manager = ConfigManager()

# Подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Глобальные переменные
request_repository: Optional[RequestRepository] = None
command_bus: Optional[CommandBus] = None

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
        logger.info("🚀 Инициализация Request Processor API...")
        
        # Инициализируем репозиторий запросов
        request_repository = RequestRepository()
        
        # Инициализируем шину команд
        command_bus = CommandBus()
        
        # Регистрируем обработчики команд
        command_bus.register_handler(
            ProcessRequestCommand,
            ProcessRequestCommandHandler(request_repository)
        )
        
        logger.info("✅ Request Processor API готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Request Processor API: {e}")
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
            dependencies={},
            error=str(e)
        )


@app.post("/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """Обработать запрос через шину команд"""
    start_time = time.time()
    
    try:
        if command_bus is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Создаем команду
        command = ProcessRequestCommand(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            services=request.services
        )
        
        # Выполняем команду
        result = await command_bus.execute(command)
        
        duration = time.time() - start_time
        
        return ProcessResponse(
            success=True,
            request_id=result.get("request_id"),
            results=result.get("results", {}),
            processing_time=duration,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Ошибка обработки запроса: {e}")
        
        return ProcessResponse(
            success=False,
            processing_time=duration,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


class CheckTextRequest(BaseModel):
    """Запрос на проверку текста"""
    query: str
    user_id: Optional[str] = None


@app.post("/check-text")
async def check_text(request: CheckTextRequest):
    """Проверка текста на экстремизм"""
    start_time = time.time()
    
    try:
        query = request.query.lower().strip()
        logger.info(f"🔍 Проверка текста: '{query}'")
        
        # 1. Поиск в векторной базе
        results = {}
        selected_document = None
        
        try:
            async with httpx.AsyncClient() as client:
                vector_response = await client.post(
                    f"{SERVICES['vectorstore']}/search",
                    json={"query": query, "top_k": 5},
                    timeout=5.0
                )
                
                if vector_response.status_code == 200:
                    vector_data = vector_response.json()
                    results["vectorstore"] = vector_data
                    
                    # Выбираем наиболее релевантный документ
                    vector_results = vector_data.get("results", [])
                    if vector_results:
                        selected_document = vector_results[0]  # Берем первый (самый релевантный)
                        logger.info(f"🎯 Выбранный документ: relevance_score={selected_document.get('relevance_score')}, text={selected_document.get('text', '')[:100]}...")
                else:
                    results["vectorstore"] = {"error": "Vector store unavailable"}
                    
        except Exception as e:
            results["vectorstore"] = {"error": str(e)}
        
        # 2. Анализ AI моделью
        if selected_document:
            try:
                context_text = selected_document.get("text", "")
                
                # Создаем промпт для AI
                ai_prompt = f"""Ты - эксперт по анализу экстремистских материалов. Определи СМЫСЛОВУЮ связь между запросом и материалом.

ВАЖНО: Семантическая близость слов НЕ означает смысловую связь!

Запрос: "{query}"
Материал: {context_text}

ПРОАНАЛИЗИРУЙ:
1. Ищет ли пользователь именно этот материал/автора?
2. Есть ли прямая связь между темой запроса и содержанием материала?
3. Или это случайное совпадение слов?

ОТВЕТЬ: Да/Нет - [объяснение]"""

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
        processing_time = time.time() - start_time
        logger.error(f"Ошибка проверки текста: {e}")
        
        return {
            "success": False,
            "is_extremist": False,
            "confidence": 0.0,
            "reason": f"Ошибка обработки: {str(e)}",
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@app.get("/requests/{request_id}")
async def get_request(request_id: str):
    """Получить информацию о запросе"""
    try:
        if request_repository is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        request = request_repository.find_by_id(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return {
            "request_id": request.id,
            "query": request.query,
            "status": request.status,
            "created_at": request.created_at.isoformat(),
            "processing_time": request.processing_time
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения запроса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/requests/user/{user_id}")
async def get_user_requests(user_id: str, limit: int = 10):
    """Получить запросы пользователя"""
    try:
        if request_repository is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        requests = request_repository.find_by_user_id(user_id, limit=limit)
        
        return {
            "user_id": user_id,
            "requests": [
                {
                    "request_id": req.id,
                    "query": req.query,
                    "status": req.status,
                    "created_at": req.created_at.isoformat()
                }
                for req in requests
            ],
            "total": len(requests)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения запросов пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics")
async def get_statistics():
    """Получить статистику запросов"""
    try:
        if request_repository is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        all_requests = request_repository.find_all()
        
        return {
            "total_requests": len(all_requests),
            "successful_requests": len([r for r in all_requests if r.status == "completed"]),
            "failed_requests": len([r for r in all_requests if r.status == "failed"]),
            "average_processing_time": sum(r.processing_time for r in all_requests) / len(all_requests) if all_requests else 0
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/services/{service_name}/health")
async def check_service_health(service_name: str):
    """Проверить здоровье конкретного сервиса"""
    try:
        if service_name not in SERVICES:
            raise HTTPException(status_code=404, detail="Service not found")
        
        service_url = SERVICES[service_name]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{service_url}/health", timeout=5.0)
            
            return {
                "service": service_name,
                "url": service_url,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code
            }
            
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья сервиса {service_name}: {e}")
        return {
            "service": service_name,
            "url": SERVICES.get(service_name, "unknown"),
            "status": "unhealthy",
            "error": str(e)
        } 