"""
AI Model Service API - полностью независимый микросервис
"""
import asyncio
import logging
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psutil

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from domain.services.model_service import ModelService
from infrastructure.persistence.optimized_model_repository import OptimizedModelRepository
from application.use_cases.generate_text import GenerateTextUseCase, GenerateTextRequest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Model Service", version="2.0.0")

model_service: Optional[ModelService] = None
generate_text_use_case: Optional[GenerateTextUseCase] = None

thread_pool: Optional[ThreadPoolExecutor] = None
process_pool: Optional[ProcessPoolExecutor] = None

MAX_WORKERS = int(os.getenv("MAX_WORKERS", "8"))
MAX_PROCESSES = int(os.getenv("MAX_PROCESSES", "2"))


class ModelRequest(BaseModel):
    """Запрос для генерации ответа"""
    query: str
    context: List[str] = []
    max_length: int = 512
    temperature: float = 0.7
    model_id: str = "qwen-model_full"
    use_async: bool = True


class ModelResponse(BaseModel):
    """Ответ модели"""
    success: bool
    result: str
    processing_time: float
    timestamp: str
    model_id: Optional[str] = None
    error: Optional[str] = None
    memory_usage: Optional[Dict[str, Any]] = None


class ModelInfo(BaseModel):
    """Информация о модели"""
    model_id: str
    name: str
    type: str
    device: str
    is_loaded: bool
    memory_usage: Optional[Dict[str, Any]] = None


class SystemInfo(BaseModel):
    """Информация о системе"""
    cpu_count: int
    memory_total: float
    memory_available: float
    memory_percent: float
    thread_pool_workers: int
    process_pool_workers: int
    loaded_models_count: int


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global model_service, generate_text_use_case, thread_pool, process_pool
    
    try:
        logger.info("🚀 Инициализация AI Model Service...")
        
        model_repository = OptimizedModelRepository()
        
        model_service = ModelService(model_repository)
        
        generate_text_use_case = GenerateTextUseCase(model_service)
        
        thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        process_pool = ProcessPoolExecutor(max_workers=MAX_PROCESSES)
        
        logger.info("✅ AI Model Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации AI Model Service: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    global thread_pool, process_pool
    
    try:
        logger.info("🛑 Завершение работы AI Model Service...")
        
        if thread_pool:
            thread_pool.shutdown(wait=True)
        
        if process_pool:
            process_pool.shutdown(wait=True)
        
        logger.info("✅ AI Model Service завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка завершения AI Model Service: {e}")


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        if model_service is None:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        loaded_models = model_service.get_loaded_models()
        
        return {
            "status": "healthy",
            "service": "ai-model",
            "timestamp": datetime.now().isoformat(),
            "loaded_models_count": len(loaded_models),
            "memory_usage": model_service.get_memory_usage()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/system-info", response_model=SystemInfo)
async def get_system_info():
    """Получить информацию о системе"""
    try:
        memory = psutil.virtual_memory()
        
        return SystemInfo(
            cpu_count=psutil.cpu_count(),
            memory_total=memory.total / 1024 / 1024 / 1024,  # GB
            memory_available=memory.available / 1024 / 1024 / 1024,  # GB
            memory_percent=memory.percent,
            thread_pool_workers=MAX_WORKERS,
            process_pool_workers=MAX_PROCESSES,
            loaded_models_count=len(model_service.get_loaded_models()) if model_service else 0
        )
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load-model")
async def load_model(model_id: str = "qwen-model_full", device: str = "auto"):
    """Загрузить модель"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        logger.info(f"Загружаем модель: {model_id}")
        model = model_service.load_model(model_id, device)
        
        return {
            "success": True,
            "model_id": model.id,
            "name": model.name,
            "device": model.device,
            "is_loaded": model.is_loaded
        }
        
    except Exception as e:
        logger.error(f"Ошибка загрузки модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/unload-model")
async def unload_model(model_id: str):
    """Выгрузить модель"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        logger.info(f"Выгружаем модель: {model_id}")
        success = model_service.unload_model(model_id)
        
        return {
            "success": success,
            "model_id": model_id
        }
        
    except Exception as e:
        logger.error(f"Ошибка выгрузки модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=ModelResponse)
async def generate_response(request: ModelRequest):
    """Генерировать ответ с помощью модели"""
    try:
        if generate_text_use_case is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        logger.info(f"Генерируем ответ для модели: {request.model_id}")
        
        use_case_request = GenerateTextRequest(
            query=request.query,
            context=request.context,
            max_length=request.max_length,
            temperature=request.temperature,
            model_id=request.model_id
        )
        
        response = generate_text_use_case.execute(use_case_request)
        
        memory_usage = model_service.get_memory_usage() if model_service else None
        
        return ModelResponse(
            success=response.success,
            result=response.result,
            processing_time=response.processing_time,
            timestamp=datetime.now().isoformat(),
            model_id=response.model_id,
            error=response.error,
            memory_usage=memory_usage
        )
        
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models", response_model=List[ModelInfo])
async def get_models():
    """Получить список всех моделей"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        models = model_service.get_loaded_models()
        
        result = []
        for model in models:
            model_info = model_service.get_model_info(model.id)
            if model_info:
                result.append(ModelInfo(**model_info))
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка получения моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/{model_id}")
async def get_model_info(model_id: str):
    """Получить информацию о конкретной модели"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        model_info = model_service.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return model_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения информации о модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize-memory")
async def optimize_memory():
    """Оптимизировать использование памяти"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        logger.info("Оптимизируем память...")
        model_service.optimize_memory()
        
        return {
            "success": True,
            "message": "Memory optimized successfully"
        }
        
    except Exception as e:
        logger.error(f"Ошибка оптимизации памяти: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory-usage")
async def get_memory_usage():
    """Получить информацию об использовании памяти"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        return model_service.get_memory_usage()
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о памяти: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
