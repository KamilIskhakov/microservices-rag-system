from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
from typing import Optional
from middleware.security import security_middleware
from services.logger import logger
from config import settings

router = APIRouter()

class CheckRequestModel(BaseModel):
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class CheckResponseModel(BaseModel):
    result: str
    processing_time: float
    device_info: dict
    confidence: float
    extremist_reason: str = ""  # Добавляем поле для причины

def get_rag_service():
    """Получает глобальный экземпляр RAG сервиса"""
    from app import rag_service
    if rag_service is None:
        raise HTTPException(status_code=503, detail="Сервис не инициализирован")
    return rag_service



@router.post("/check", response_model=CheckResponseModel)
async def check_extremist_materials(
    request: CheckRequestModel, 
    response: Response,
    http_request: Request
):
    """Проверяет запрос на наличие экстремистских материалов"""
    try:
        # Логируем POST запрос
        client_ip = http_request.client.host if hasattr(http_request, 'client') else "unknown"
        user_agent = http_request.headers.get('user-agent', 'unknown')
        origin = http_request.headers.get('origin', 'unknown')
        logger.info(f"POST request received from {client_ip}")
        logger.info(f"User-Agent: {user_agent}")
        logger.info(f"Origin: {origin}")
        logger.info(f"Request headers: {dict(http_request.headers)}")
        
        # Проверяем rate limiting
        if not security_middleware.check_rate_limit(client_ip):
            raise HTTPException(
                status_code=429, 
                detail="Превышен лимит запросов. Попробуйте позже."
            )
        
        # Валидируем входные данные только для POST запросов
        if http_request.method == "POST":
            if not security_middleware.validate_input(request.dict()):
                raise HTTPException(
                    status_code=400, 
                    detail="Недопустимые входные данные"
                )
        
        # Добавляем заголовки безопасности
        security_middleware.add_security_headers(response)
        
        # Отключаем кеширование
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # Логируем запрос (без чувствительных данных)
        sanitized_query = security_middleware.sanitize_log_data(request.query)
        logger.info(f"Processing check request: query_length={len(request.query)}")
        
        rag = get_rag_service()
        
        # Создаем запрос
        from services.rag_service import CheckRequest
        check_request = CheckRequest(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Выполняем проверку
        response_data = rag.check(check_request)
        
        logger.info(f"Check completed: result={response_data.result}, processing_time={response_data.processing_time:.2f}s")
        
        return CheckResponseModel(
            result=response_data.result,
            processing_time=response_data.processing_time,
            device_info=response_data.device_info,
            confidence=response_data.confidence,
            extremist_reason=response_data.extremist_reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing check request: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/health")
async def health_check(response: Response):
    """Проверка здоровья сервиса"""
    try:
        # Добавляем заголовки безопасности
        security_middleware.add_security_headers(response)
        
        logger.info("Health check requested")
        rag = get_rag_service()
        health_status = rag.get_health_status()
        
        # Убираем чувствительную информацию
        safe_health_status = {
            "status": health_status.get("status", "unknown"),
            "device": health_status.get("device", "unknown"),
            "model_loaded": health_status.get("model_loaded", False),
            "vector_store_loaded": health_status.get("vector_store_loaded", False)
        }
        
        logger.info(f"Health check completed: {safe_health_status['status']}")
        return safe_health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": "Internal server error"}

@router.get("/statistics")
async def get_statistics(response: Response):
    """Получение статистики сервиса"""
    try:
        # Добавляем заголовки безопасности
        security_middleware.add_security_headers(response)
        
        logger.info("Statistics requested")
        rag = get_rag_service()
        stats = rag.get_statistics()
        
        # Убираем чувствительную информацию
        safe_stats = {
            "total_requests": stats.get("total_requests", 0),
            "successful_requests": stats.get("successful_requests", 0),
            "failed_requests": stats.get("failed_requests", 0),
            "average_response_time": stats.get("average_response_time", 0.0),
            "last_request_time": stats.get("last_request_time", None)
        }
        
        logger.info(f"Statistics retrieved: {safe_stats['total_requests']} total requests")
        return safe_stats
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {e}")
        return {"error": "Failed to retrieve statistics"}