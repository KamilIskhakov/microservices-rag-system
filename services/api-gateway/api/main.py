"""
API Gateway Service - полностью независимый микросервис
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Добавляем путь к доменной логике
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импорты доменной логики
from domain.services.gateway_service import GatewayService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway Service", version="2.0.0")

# Глобальные переменные
gateway_service: Optional[GatewayService] = None


class ServiceHealthResponse(BaseModel):
    """Ответ о здоровье сервиса"""
    service: str
    status: str
    response_time: Optional[float] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class GatewayResponse(BaseModel):
    """Ответ API Gateway"""
    success: bool
    request_id: Optional[str] = None
    target_service: Optional[str] = None
    status_code: Optional[int] = None
    body: Optional[Dict[str, Any]] = None
    processing_time: float
    timestamp: str
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global gateway_service
    
    try:
        logger.info("🚀 Инициализация API Gateway Service...")
        
        # Инициализируем доменный сервис
        gateway_service = GatewayService()
        
        logger.info("✅ API Gateway Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации API Gateway Service: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    global gateway_service
    
    try:
        if gateway_service:
            await gateway_service.close()
        logger.info("✅ API Gateway Service завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка завершения API Gateway Service: {e}")


@app.get("/health")
async def health_check():
    """Проверка здоровья API Gateway"""
    try:
        if gateway_service is None:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        # Проверяем здоровье всех сервисов
        services_health = await gateway_service.check_all_services_health()
        
        # Определяем общий статус
        all_healthy = all(
            health.get("status") == "healthy" 
            for health in services_health.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "service": "api-gateway",
            "timestamp": datetime.now().isoformat(),
            "services": services_health
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.get("/services")
async def get_services_info():
    """Получить информацию о всех сервисах"""
    try:
        if gateway_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        services = gateway_service.get_all_services_info()
        
        result = {}
        for name, service in services.items():
            result[name] = {
                "name": service.name,
                "url": service.url,
                "is_available": service.is_available,
                "last_check": service.last_check.isoformat() if service.last_check else None,
                "response_time": service.response_time
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о сервисах: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/services/{service_name}/health")
async def check_service_health(service_name: str):
    """Проверить здоровье конкретного сервиса"""
    try:
        if gateway_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        health_data = await gateway_service.check_service_health(service_name)
        
        return ServiceHealthResponse(**health_data)
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья сервиса {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_request(request: Request, path: str):
    """Маршрутизировать запрос к соответствующему сервису"""
    try:
        if gateway_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        # Получаем данные запроса
        method = request.method
        headers = dict(request.headers)
        body = None
        
        if method in ["POST", "PUT"]:
            try:
                body = await request.json()
            except:
                body = {}
        
        # Извлекаем user_id и session_id из заголовков
        user_id = headers.get("X-User-ID")
        session_id = headers.get("X-Session-ID")
        
        logger.info(f"Маршрутизируем запрос {method} /{path}")
        
        # Маршрутизируем запрос
        result = await gateway_service.route_request(
            method=method,
            path=f"/{path}",
            headers=headers,
            body=body,
            user_id=user_id,
            session_id=session_id
        )
        
        processing_time = time.time() - start_time
        
        if result["success"]:
            return JSONResponse(
                status_code=result["status_code"],
                content=result["body"]
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "error": result["error"],
                    "request_id": result["request_id"],
                    "processing_time": processing_time
                }
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Ошибка маршрутизации запроса: {e}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "processing_time": processing_time
            }
        )


@app.get("/statistics")
async def get_statistics():
    """Получить статистику API Gateway"""
    try:
        if gateway_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Получаем информацию о сервисах
        services = gateway_service.get_all_services_info()
        
        available_services = sum(1 for s in services.values() if s.is_available)
        total_services = len(services)
        
        return {
            "total_services": total_services,
            "available_services": available_services,
            "unavailable_services": total_services - available_services,
            "uptime_percentage": (available_services / total_services * 100) if total_services > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "API Gateway",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "services": "/services",
            "service_health": "/services/{service_name}/health",
            "statistics": "/statistics"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
