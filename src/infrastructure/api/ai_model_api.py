"""
AI Model API - FastAPI приложение
Использует доменную логику из src/
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

# Импорты доменной логики
from src.domain.services.model_service import ModelService
from src.infrastructure.persistence.optimized_model_repository import OptimizedModelRepository
from src.domain.observers.model_observer import ModelEventManager
from src.shared.config.config_manager import ConfigManager
from src.infrastructure.factories.device_factory import DeviceFactory

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Model API", version="1.0.0")

# Инициализируем конфигурацию
config_manager = ConfigManager()
device_factory = DeviceFactory(config_manager)

# Глобальные переменные
model_service: Optional[ModelService] = None
event_manager: Optional[ModelEventManager] = None

# Пул потоков для генерации
thread_pool: Optional[ThreadPoolExecutor] = None
process_pool: Optional[ProcessPoolExecutor] = None

# Конфигурация из переменных окружения
MAX_WORKERS = config_manager.get_max_workers()
MAX_PROCESSES = config_manager.get_max_processes()


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
    global model_service, event_manager, thread_pool, process_pool
    
    try:
        logger.info("🚀 Инициализация AI Model API...")
        
        # Инициализируем пулы потоков и процессов
        thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="ai_worker")
        process_pool = ProcessPoolExecutor(max_workers=MAX_PROCESSES)
        
        logger.info(f"📊 Инициализированы пулы: ThreadPool({MAX_WORKERS}), ProcessPool({MAX_PROCESSES})")
        
        # Инициализируем менеджер событий
        event_manager = ModelEventManager()
        
        # Инициализируем репозиторий и сервис
        model_repository = OptimizedModelRepository(event_manager)
        model_service = ModelService(model_repository)
        
        # Логируем конфигурацию
        config_manager.log_configuration()
        
        # Проверяем доступные устройства
        device_validation = device_factory.validate_all_devices()
        logger.info(f"🔍 Валидация устройств: {device_validation}")
        
        logger.info("✅ AI Model API инициализирован")
        
        # Автоматически загружаем модель по умолчанию
        try:
            logger.info("🔄 Автоматическая загрузка модели по умолчанию...")
            model_name = config_manager.get_model_config()["name"]
            device_type = config_manager.get_optimal_device()
            await load_model(model_name, device_type)
            logger.info("✅ Модель загружена автоматически")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось автоматически загрузить модель: {e}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при выключении"""
    global thread_pool, process_pool
    
    logger.info("🛑 Завершение работы AI Model API...")
    
    if thread_pool:
        thread_pool.shutdown(wait=True)
        logger.info("✅ ThreadPool завершен")
    
    if process_pool:
        process_pool.shutdown(wait=True)
        logger.info("✅ ProcessPool завершен")


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        if model_service is None:
            return {"status": "unhealthy", "service": "ai-model", "error": "Service not initialized"}
        
        loaded_models = model_service.get_loaded_models()
        memory_usage = model_service.get_memory_usage()
        
        return {
            "status": "healthy",
            "service": "ai-model",
            "loaded_models_count": len(loaded_models),
            "memory_usage": memory_usage,
            "thread_pool_active": thread_pool._work_queue.qsize() if thread_pool else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "service": "ai-model", "error": str(e)}


@app.get("/system-info", response_model=SystemInfo)
async def get_system_info():
    """Получить информацию о системе"""
    try:
        memory_info = psutil.virtual_memory()
        loaded_models = model_service.get_loaded_models() if model_service else []
        
        return SystemInfo(
            cpu_count=os.cpu_count() or 1,
            memory_total=memory_info.total / (1024**3),
            memory_available=memory_info.available / (1024**3),
            memory_percent=memory_info.percent,
            thread_pool_workers=MAX_WORKERS,
            process_pool_workers=MAX_PROCESSES,
            loaded_models_count=len(loaded_models)
        )
    except Exception as e:
        logger.error(f"Ошибка получения информации о системе: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load-model")
async def load_model(model_id: str = "qwen-model_full", device: str = "auto"):
    """Загрузить модель асинхронно"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Получаем путь к модели
        model_path = config_manager.get_model_path()
        
        # Выполняем загрузку в отдельном потоке
        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(thread_pool, model_service.model_repository.load_model, model_path, device)
        
        return {
            "success": True,
            "model_id": model.id,
            "message": f"Модель {model.name} загружена успешно"
        }
        
    except Exception as e:
        logger.error(f"Ошибка загрузки модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/unload-model")
async def unload_model(model_id: str):
    """Выгрузить модель асинхронно"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Выполняем выгрузку в отдельном потоке
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(thread_pool, model_service.unload_model, model_id)
        
        if success:
            return {
                "success": True,
                "message": f"Модель {model_id} выгружена успешно"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found or not loaded")
        
    except Exception as e:
        logger.error(f"Ошибка выгрузки модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_response_async(model_id: str, prompt: str, max_length: int, temperature: float) -> str:
    """Асинхронная генерация ответа с оптимизацией CPU"""
    loop = asyncio.get_event_loop()
    
    # Используем ThreadPoolExecutor с torch.set_num_threads
    result = await loop.run_in_executor(
        thread_pool, 
        model_service.model_repository.generate_text,
        model_id, prompt, max_length, temperature
    )
    return result


@app.post("/generate", response_model=ModelResponse)
async def generate_response(request: ModelRequest):
    """Генерировать ответ с многопоточностью"""
    start_time = time.time()
    
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Проверяем доступность модели
        if not model_service.is_model_available(request.model_id):
            raise HTTPException(status_code=503, detail=f"Model {request.model_id} not loaded")
        
        # Выполняем генерацию с таймаутом
        try:
            if request.use_async:
                result = await asyncio.wait_for(
                    generate_response_async(request.model_id, request.query, request.max_length, request.temperature), 
                    timeout=config_manager.get_max_generation_time()
                )
            else:
                # Синхронная генерация в отдельном потоке
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        thread_pool, 
                        model_service.model_repository.generate_text,
                        request.model_id, request.query, request.max_length, request.temperature
                    ),
                    timeout=config_manager.get_max_generation_time()
                )
            
            logger.info("✅ Генерация завершена успешно")
            
        except asyncio.TimeoutError:
            logger.error("❌ Генерация превысила таймаут")
            raise HTTPException(status_code=408, detail="Generation timeout")
        except Exception as e:
            logger.error(f"❌ Ошибка генерации: {e}")
            raise HTTPException(status_code=500, detail=f"Generation error: {e}")
        
        duration = time.time() - start_time
        
        # Получаем информацию о памяти
        memory_usage = model_service.get_memory_usage()
        
        response = ModelResponse(
            success=True,
            result=result,
            processing_time=duration,
            timestamp=datetime.now().isoformat(),
            model_id=request.model_id,
            memory_usage=memory_usage
        )
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Ошибка генерации: {e}")
        
        return ModelResponse(
            success=False,
            result="",
            processing_time=duration,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@app.get("/models", response_model=List[ModelInfo])
async def get_models():
    """Получить список моделей"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        models = model_service.model_repository.find_all()
        
        return [
            ModelInfo(
                model_id=model.id,
                name=model.name,
                type=model.type,
                device=model.device,
                is_loaded=model.is_loaded,
                memory_usage=model_service.get_memory_usage() if model.is_loaded else None
            )
            for model in models
        ]
        
    except Exception as e:
        logger.error(f"Ошибка получения списка моделей: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/{model_id}")
async def get_model_info(model_id: str):
    """Получить информацию о модели"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        info = model_service.get_model_info(model_id)
        if not info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return info
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize-memory")
async def optimize_memory():
    """Оптимизировать память"""
    try:
        if model_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Выполняем оптимизацию в отдельном потоке
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(thread_pool, model_service.optimize_memory)
        
        return {
            "success": True,
            "message": "Память оптимизирована",
            "timestamp": datetime.now().isoformat()
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