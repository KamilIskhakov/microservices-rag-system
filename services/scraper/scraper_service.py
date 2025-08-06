"""
Scraper Service - парсинг данных Минюста
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

import redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.domain.entities.scraped_data import ScrapedData
from src.infrastructure.persistence.file_scraper_repository import FileScraperRepository as ScraperRepository
from src.application.commands.scraper_commands import (
    StartScrapingCommand,
    StartScrapingCommandHandler,
    GetScrapingStatusCommand,
    GetScrapingStatusCommandHandler,
    CommandBus
)
from src.shared.utils.logger import logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logger

app = FastAPI(title="RAG Scraper Service", version="2.0.0")

# Подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Глобальные переменные
scraper_repository: Optional[ScraperRepository] = None
command_bus: Optional[CommandBus] = None

class ScrapingRequest(BaseModel):
    """Запрос на запуск парсинга"""
    source: str = "minjust"  # Источник данных
    force_update: bool = False  # Принудительное обновление
    max_items: Optional[int] = None  # Максимальное количество элементов

class ScrapingResponse(BaseModel):
    """Ответ на запуск парсинга"""
    success: bool
    job_id: Optional[str] = None
    message: str = ""
    timestamp: str
    error: Optional[str] = None

class ScrapingStatus(BaseModel):
    """Статус парсинга"""
    job_id: str
    status: str  # "running", "completed", "failed"
    progress: float = 0.0
    items_processed: int = 0
    items_total: int = 0
    start_time: str = ""
    end_time: Optional[str] = None
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
    global scraper_repository, command_bus
    
    try:
        logger.info("🚀 Инициализация Scraper Service...")
        
        # Инициализируем репозиторий скрапера
        scraper_repository = ScraperRepository()
        
        # Инициализируем шину команд
        command_bus = CommandBus()
        
        # Регистрируем обработчики команд
        command_bus.register_handler(
            StartScrapingCommand,
            StartScrapingCommandHandler(scraper_repository)
        )
        
        command_bus.register_handler(
            GetScrapingStatusCommand,
            GetScrapingStatusCommandHandler(scraper_repository)
        )
        
        logger.info("✅ Scraper Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Scraper Service: {e}")
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
        
        dependencies = {
            "redis": redis_healthy,
            "minjust_api": "unknown"  # Будет проверяться через HTTP
        }
        
        return HealthResponse(
            status="healthy" if redis_healthy == "healthy" else "unhealthy",
            service="scraper",
            timestamp=datetime.now().isoformat(),
            dependencies=dependencies
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="scraper",
            timestamp=datetime.now().isoformat(),
            dependencies={"error": str(e)}
        )

@app.post("/start-scraping", response_model=ScrapingResponse)
async def start_scraping(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """Запуск парсинга данных"""
    try:
        logger.info(f"🕷️ Запуск парсинга из источника: {request.source}")
        
        # Создаем команду для запуска парсинга
        command = StartScrapingCommand(
            source=request.source,
            force_update=request.force_update,
            max_items=request.max_items
        )
        
        # Отправляем команду через шину команд
        result = await command_bus.handle(command)
        
        # Добавляем задачу в фоновые задачи
        background_tasks.add_task(run_scraping_job, result.job_id)
        
        return ScrapingResponse(
            success=True,
            job_id=result.job_id,
            message=f"Парсинг запущен с job_id: {result.job_id}",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска парсинга: {e}")
        
        return ScrapingResponse(
            success=False,
            message="Ошибка запуска парсинга",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

async def run_scraping_job(job_id: str):
    """Выполнение задачи парсинга в фоне"""
    try:
        logger.info(f"🔄 Выполнение задачи парсинга {job_id}")
        
        # Обновляем статус на "running"
        scraper_repository.update_job_status(job_id, "running")
        
        # Импортируем парсер
        from minjust_scraper import MinjustScraper
        
        # Выполняем парсинг
        scraper = MinjustScraper()
        materials = scraper.scrape_to_scraped_data()  # Парсим все доступные страницы
        
        # Сохраняем данные в репозиторий
        logger.info(f"💾 Сохранение {len(materials)} материалов в репозиторий...")
        for i, material in enumerate(materials):
            scraper_repository.save_data(material)
            # Обновляем прогресс каждые 100 элементов
            if i % 100 == 0:
                progress = (i + 1) / len(materials) * 0.5  # 50% на сохранение
                scraper_repository.update_job_status(job_id, "running", progress=progress, items_processed=i+1, items_total=len(materials))
        
        # Интегрируем с RAG системой только если включено
        from config import scraper_settings
        if scraper_settings.RAG_INTEGRATION_ENABLED:
            logger.info(f"🔗 Интеграция с RAG системой для {len(materials)} материалов...")
            from rag_integration import RAGIntegration
            rag_integration = RAGIntegration()
            await rag_integration.add_scraped_data_to_rag(materials)
            logger.info("✅ RAG интеграция завершена")
        else:
            logger.info("RAG integration disabled, skipping vector store update")
        
        # Обновляем статус задачи
        scraper_repository.update_job_status(job_id, "completed", progress=1.0, items_processed=len(materials), items_total=len(materials))
        
        logger.info(f"✅ Задача парсинга {job_id} завершена. Обработано {len(materials)} материалов")
        
    except Exception as e:
        logger.error(f"❌ Ошибка выполнения задачи парсинга {job_id}: {e}")
        scraper_repository.update_job_status(job_id, "failed")

@app.get("/status/{job_id}", response_model=ScrapingStatus)
async def get_scraping_status(job_id: str):
    """Получение статуса задачи парсинга"""
    try:
        logger.info(f"📊 Получение статуса задачи {job_id}")
        
        # Создаем команду для получения статуса
        command = GetScrapingStatusCommand(job_id=job_id)
        
        # Отправляем команду через шину команд
        result = await command_bus.handle(command)
        
        return ScrapingStatus(
            job_id=job_id,
            status=result.status,
            progress=result.progress,
            items_processed=result.items_processed,
            items_total=result.items_total,
            start_time=result.start_time,
            end_time=result.end_time,
            error=result.error
        )
        
    except Exception as e:
        logger.error(f"Error getting scraping status for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs")
async def get_all_jobs():
    """Получение всех задач парсинга"""
    try:
        jobs = scraper_repository.get_all_jobs()
        
        return {
            "success": True,
            "jobs": [
                {
                    "job_id": job.job_id,
                    "status": job.status,
                    "source": job.source,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in jobs
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting all jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/latest")
async def get_latest_data():
    """Получение последних данных"""
    try:
        data = scraper_repository.get_latest_data()
        
        return {
            "success": True,
            "data": [
                {
                    "id": item.id,
                    "title": item.title,
                    "court_name": item.court_name,
                    "court_date": item.court_date.isoformat(),
                    "material_name": item.material_name,
                    "created_at": item.created_at.isoformat()
                }
                for item in data
            ],
            "count": len(data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting latest data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/count")
async def get_data_count():
    """Получение количества данных"""
    try:
        count = scraper_repository.get_data_count()
        
        return {
            "success": True,
            "count": count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting data count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/data/export")
async def export_data():
    """Экспорт данных"""
    try:
        logger.info("📤 Экспорт данных...")
        
        # Здесь должна быть логика экспорта
        # Пока возвращаем заглушку
        
        return {
            "success": True,
            "message": "Экспорт данных запущен",
            "export_id": "export_123",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Отмена задачи парсинга"""
    try:
        success = scraper_repository.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "success": True,
            "message": f"Job {job_id} cancelled successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Получение статистики скрапера"""
    try:
        stats = scraper_repository.get_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/sync-all")
async def sync_all_to_rag():
    """Принудительная синхронизация всех данных с RAG системой батчами"""
    try:
        logger.info("🔄 Начинаем синхронизацию всех данных с RAG системой...")
        
        # Получаем все данные из репозитория
        all_data = scraper_repository.get_all_data()  # Получаем все данные
        
        logger.info(f"📊 Найдено {len(all_data)} документов для синхронизации")
        
        if not all_data:
            return {
                "success": False,
                "message": "Нет данных для синхронизации",
                "timestamp": datetime.now().isoformat()
            }
        
        # Интегрируем с RAG системой
        from config import scraper_settings
        if scraper_settings.RAG_INTEGRATION_ENABLED:
            from rag_integration import RAGIntegration
            rag_integration = RAGIntegration()
            
            # Разбиваем на батчи по 100 документов
            batch_size = 100
            total_batches = (len(all_data) + batch_size - 1) // batch_size
            total_synced = 0
            
            for i in range(0, len(all_data), batch_size):
                batch = all_data[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"📦 Обрабатываем батч {batch_num}/{total_batches} ({len(batch)} документов)")
                
                # Синхронизируем батч
                success = await rag_integration.add_scraped_data_to_rag(batch)
                
                if success:
                    total_synced += len(batch)
                    logger.info(f"✅ Батч {batch_num} синхронизирован ({total_synced}/{len(all_data)})")
                else:
                    logger.error(f"❌ Ошибка синхронизации батча {batch_num}")
                    return {
                        "success": False,
                        "message": f"Ошибка синхронизации батча {batch_num}",
                        "timestamp": datetime.now().isoformat()
                    }
            
            logger.info(f"✅ Успешно синхронизировано {total_synced} документов с RAG")
            return {
                "success": True,
                "message": f"Синхронизировано {total_synced} документов в {total_batches} батчах",
                "documents_count": total_synced,
                "batches_processed": total_batches,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.warning("RAG integration disabled")
            return {
                "success": False,
                "message": "RAG integration disabled",
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации с RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 