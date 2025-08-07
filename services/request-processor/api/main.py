"""
Request Processor Service API - полностью независимый микросервис
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from domain.services.request_service import RequestService
from infrastructure.persistence.in_memory_repository import InMemoryRequestRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Request Processor Service", version="2.0.0")

request_service: Optional[RequestService] = None


class ProcessRequest(BaseModel):
    """Запрос на обработку"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    services: Optional[List[str]] = None


class ProcessResponse(BaseModel):
    """Ответ на обработку"""
    success: bool
    request_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    processing_time: float
    timestamp: str
    error: Optional[str] = None


class RequestInfo(BaseModel):
    """Информация о запросе"""
    id: str
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    status: str
    created_at: str
    updated_at: str
    processing_time: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class StatisticsResponse(BaseModel):
    """Ответ со статистикой"""
    total_requests: int
    completed_requests: int
    failed_requests: int
    pending_requests: int
    avg_processing_time: float
    unique_users: int


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global request_service
    
    try:
        logger.info("🚀 Инициализация Request Processor Service...")
        
        request_repository = InMemoryRequestRepository()
        
        request_service = RequestService(request_repository)
        
        logger.info("✅ Request Processor Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Request Processor Service: {e}")
        raise


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        if request_service is None:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        stats = request_service.get_statistics()
        
        return {
            "status": "healthy",
            "service": "request-processor",
            "timestamp": datetime.now().isoformat(),
            "total_requests": stats["total_requests"],
            "completed_requests": stats["completed_requests"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.post("/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """Обработать запрос"""
    try:
        if request_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Обрабатываем запрос: {request.query[:50]}...")
        
        result = await request_service.process_request(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            services=request.services
        )
        
        processing_time = time.time() - start_time
        
        if "error" in result:
            return ProcessResponse(
                success=False,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                error=result["error"]
            )
        else:
            return ProcessResponse(
                success=True,
                request_id=result["request_id"],
                results=result["results"],
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Ошибка обработки запроса: {e}")
        
        return ProcessResponse(
            success=False,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@app.get("/request/{request_id}", response_model=RequestInfo)
async def get_request(request_id: str):
    """Получить запрос по ID"""
    try:
        if request_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        request = request_service.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return RequestInfo(
            id=request.id,
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            status=request.status,
            created_at=request.created_at.isoformat(),
            updated_at=request.updated_at.isoformat(),
            processing_time=request.processing_time,
            results=request.results,
            error=request.error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения запроса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/requests")
async def get_user_requests(user_id: str, limit: int = 10):
    """Получить запросы пользователя"""
    try:
        if request_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        requests = request_service.get_user_requests(user_id, limit)
        
        result = []
        for req in requests:
            result.append({
                "id": req.id,
                "query": req.query,
                "status": req.status,
                "created_at": req.created_at.isoformat(),
                "updated_at": req.updated_at.isoformat(),
                "processing_time": req.processing_time
            })
        
        return {
            "user_id": user_id,
            "requests": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения запросов пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Получить статистику"""
    try:
        if request_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        stats = request_service.get_statistics()
        
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/request/{request_id}")
async def delete_request(request_id: str):
    """Удалить запрос"""
    try:
        if request_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        success = request_service.delete_request(request_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return {
            "success": True,
            "request_id": request_id,
            "message": "Request deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления запроса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pending-requests")
async def get_pending_requests():
    """Получить ожидающие запросы"""
    try:
        if request_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        pending_requests = request_service.request_repository.get_pending_requests()
        
        result = []
        for req in pending_requests:
            result.append({
                "id": req.id,
                "query": req.query,
                "user_id": req.user_id,
                "created_at": req.created_at.isoformat()
            })
        
        return {
            "pending_requests": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения ожидающих запросов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
