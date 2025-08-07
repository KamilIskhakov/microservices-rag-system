"""
Scraper Service API - полностью независимый микросервис
"""
import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Добавляем путь к доменной логике
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импорты доменной логики
from domain.services.scraper_service import ScraperService
from infrastructure.persistence.in_memory_repository import InMemoryScraperRepository

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Scraper Service", version="2.0.0")

# Глобальные переменные
scraper_service: Optional[ScraperService] = None


class CreateJobRequest(BaseModel):
    """Запрос на создание задачи скрапинга"""
    source_url: str
    job_type: str = "minjust"


class JobResponse(BaseModel):
    """Ответ для задачи скрапинга"""
    success: bool
    job_id: Optional[str] = None
    data_id: Optional[str] = None
    status: str
    processing_time: float
    timestamp: str
    error: Optional[str] = None


class ScrapedDataInfo(BaseModel):
    """Информация о скрапленных данных"""
    id: str
    source_url: str
    title: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    content_length: int
    error: Optional[str] = None


class ScrapingJobInfo(BaseModel):
    """Информация о задаче скрапинга"""
    id: str
    source_url: str
    job_type: str
    status: str
    priority: int
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class StatisticsResponse(BaseModel):
    """Ответ со статистикой"""
    total_scraped_data: int
    processed_data: int
    failed_data: int
    pending_data: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    pending_jobs: int
    running_jobs: int


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global scraper_service
    
    try:
        logger.info("🚀 Инициализация Scraper Service...")
        
        # Инициализируем репозиторий
        scraper_repository = InMemoryScraperRepository()
        
        # Инициализируем доменный сервис
        scraper_service = ScraperService(scraper_repository)
        
        logger.info("✅ Scraper Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Scraper Service: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    global scraper_service
    
    try:
        if scraper_service:
            await scraper_service.close()
        logger.info("✅ Scraper Service завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка завершения Scraper Service: {e}")


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        if scraper_service is None:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        # Проверяем доступность сервиса
        stats = scraper_service.get_statistics()
        
        return {
            "status": "healthy",
            "service": "scraper",
            "timestamp": datetime.now().isoformat(),
            "total_jobs": stats["total_jobs"],
            "total_scraped_data": stats["total_scraped_data"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.post("/create-job", response_model=JobResponse)
async def create_scraping_job(request: CreateJobRequest):
    """Создать задачу скрапинга"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Создаем задачу скрапинга для: {request.source_url}")
        
        # Создаем задачу
        job = await scraper_service.create_scraping_job(
            source_url=request.source_url,
            job_type=request.job_type
        )
        
        processing_time = time.time() - start_time
        
        return JobResponse(
            success=True,
            job_id=job.id,
            status="created",
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Ошибка создания задачи скрапинга: {e}")
        
        return JobResponse(
            success=False,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@app.post("/execute-job/{job_id}", response_model=JobResponse)
async def execute_scraping_job(job_id: str, background_tasks: BackgroundTasks):
    """Выполнить задачу скрапинга"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Выполняем задачу скрапинга: {job_id}")
        
        # Выполняем задачу
        result = await scraper_service.execute_scraping_job(job_id)
        
        processing_time = time.time() - start_time
        
        return JobResponse(
            success=result["success"],
            job_id=result["job_id"],
            data_id=result.get("data_id"),
            status=result["status"],
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=result.get("error")
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Ошибка выполнения задачи скрапинга: {e}")
        
        return JobResponse(
            success=False,
            job_id=job_id,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@app.get("/job/{job_id}", response_model=ScrapingJobInfo)
async def get_scraping_job(job_id: str):
    """Получить задачу скрапинга по ID"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        job = scraper_service.get_scraping_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return ScrapingJobInfo(
            id=job.id,
            source_url=job.source_url,
            job_type=job.job_type,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            error=job.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения задачи скрапинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/{data_id}", response_model=ScrapedDataInfo)
async def get_scraped_data(data_id: str):
    """Получить скрапленные данные по ID"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        data = scraper_service.get_scraped_data(data_id)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        
        return ScrapedDataInfo(
            id=data.id,
            source_url=data.source_url,
            title=data.title,
            status=data.status,
            created_at=data.created_at.isoformat(),
            updated_at=data.updated_at.isoformat(),
            content_length=len(data.content),
            error=data.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения скрапленных данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/pending")
async def get_pending_jobs():
    """Получить ожидающие задачи"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        jobs = scraper_service.get_pending_jobs()
        
        result = []
        for job in jobs:
            result.append({
                "id": job.id,
                "source_url": job.source_url,
                "job_type": job.job_type,
                "status": job.status,
                "created_at": job.created_at.isoformat()
            })
        
        return {
            "pending_jobs": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения ожидающих задач: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/running")
async def get_running_jobs():
    """Получить выполняющиеся задачи"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        jobs = scraper_service.get_running_jobs()
        
        result = []
        for job in jobs:
            result.append({
                "id": job.id,
                "source_url": job.source_url,
                "job_type": job.job_type,
                "status": job.status,
                "started_at": job.started_at.isoformat() if job.started_at else None
            })
        
        return {
            "running_jobs": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения выполняющихся задач: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data")
async def get_all_scraped_data(limit: int = 100):
    """Получить все скрапленные данные"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        data_list = scraper_service.get_all_scraped_data(limit)
        
        result = []
        for data in data_list:
            result.append({
                "id": data.id,
                "source_url": data.source_url,
                "title": data.title,
                "status": data.status,
                "created_at": data.created_at.isoformat(),
                "content_length": len(data.content)
            })
        
        return {
            "scraped_data": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения скрапленных данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Получить статистику"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        stats = scraper_service.get_statistics()
        
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/job/{job_id}")
async def delete_scraping_job(job_id: str):
    """Удалить задачу скрапинга"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        success = scraper_service.delete_scraping_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Job deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления задачи скрапинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/data/{data_id}")
async def delete_scraped_data(data_id: str):
    """Удалить скрапленные данные"""
    try:
        if scraper_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        success = scraper_service.delete_scraped_data(data_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Data not found")
        
        return {
            "success": True,
            "data_id": data_id,
            "message": "Data deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления скрапленных данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
