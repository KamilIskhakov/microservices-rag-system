from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from middleware.security import security_middleware
from services.logger import logger
from services.database_updater import UpdateResult
from services.scheduler import TaskScheduler

router = APIRouter()

class UpdateRequestModel(BaseModel):
    force: bool = False

class UpdateResponseModel(BaseModel):
    success: bool
    materials_added: int
    materials_updated: int
    materials_total: int
    duration_seconds: float
    error: Optional[str] = None
    timestamp: datetime

class TaskStatusModel(BaseModel):
    name: str
    is_running: bool
    last_run: Optional[str] = None
    error_count: int
    interval_hours: int

def get_scheduler() -> TaskScheduler:
    """Получает глобальный экземпляр планировщика"""
    from app import scheduler
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Планировщик не инициализирован")
    return scheduler

def get_updater():
    """Получает глобальный экземпляр обновлятеля БД"""
    from app import database_updater
    if database_updater is None:
        raise HTTPException(status_code=503, detail="Обновлятель БД не инициализирован")
    return database_updater


@router.post("/update", response_model=UpdateResponseModel)
async def update_database(
    request: UpdateRequestModel,
    response: Response,
    http_request: Request
):
    """Запускает обновление базы данных"""
    try:
        # Логируем запрос
        client_ip = http_request.client.host if hasattr(http_request, 'client') else "unknown"
        logger.info(f"POST /update request from {client_ip}, force={request.force}")
        
        # Проверяем rate limiting
        if not security_middleware.check_rate_limit(client_ip):
            raise HTTPException(
                status_code=429, 
                detail="Превышен лимит запросов. Попробуйте позже."
            )
        
        # Добавляем заголовки безопасности
        security_middleware.add_security_headers(response)
        
        # Получаем обновлятель БД
        updater = get_updater()
        
        # Выполняем обновление
        if request.force:
            result = await updater.force_update()
        else:
            result = await updater.update_database()
        
        logger.info(f"Database update completed: success={result.success}, added={result.materials_added}")
        
        return UpdateResponseModel(
            success=result.success,
            materials_added=result.materials_added,
            materials_updated=result.materials_updated,
            materials_total=result.materials_total,
            duration_seconds=result.duration_seconds,
            error=result.error,
            timestamp=result.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating database: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@router.get("/update/status")
async def get_update_status(response: Response):
    """Получает статус обновления базы данных"""
    try:
        # Добавляем заголовки безопасности
        security_middleware.add_security_headers(response)
        
        logger.info("GET /update/status request")
        
        updater = get_updater()
        status = await updater.get_update_status()
        
        logger.info(f"Update status retrieved: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Error getting update status: {e}")
        return {"error": "Failed to get update status"}


@router.get("/scheduler/status")
async def get_scheduler_status(response: Response):
    """Получает статус планировщика задач"""
    try:
        # Добавляем заголовки безопасности
        security_middleware.add_security_headers(response)
        
        logger.info("GET /scheduler/status request")
        
        scheduler = get_scheduler()
        status = await scheduler.get_task_status("database_update")
        
        logger.info(f"Scheduler status retrieved: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return {"error": "Failed to get scheduler status"}


@router.post("/scheduler/run")
async def run_scheduled_task(
    task_name: str = "database_update",
    response: Response = None
):
    """Запускает запланированную задачу немедленно"""
    try:
        # Добавляем заголовки безопасности
        if response:
            security_middleware.add_security_headers(response)
        
        logger.info(f"POST /scheduler/run request for task: {task_name}")
        
        scheduler = get_scheduler()
        result = await scheduler.run_task_now(task_name)
        
        if result:
            logger.info(f"Task {task_name} completed: success={result.success}")
            return {
                "success": result.success,
                "materials_added": result.materials_added,
                "materials_updated": result.materials_updated,
                "duration_seconds": result.duration_seconds,
                "error": result.error
            }
        else:
            logger.error(f"Task {task_name} failed")
            return {"success": False, "error": "Task execution failed"}
            
    except Exception as e:
        logger.error(f"Error running scheduled task: {e}")
        return {"success": False, "error": str(e)} 