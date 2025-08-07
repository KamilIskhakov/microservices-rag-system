"""
Payment Service API - полностью независимый микросервис
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

from domain.services.payment_service import PaymentService
from infrastructure.persistence.in_memory_repository import InMemoryPaymentRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payment Service", version="2.0.0")

payment_service: Optional[PaymentService] = None


class CreatePaymentRequest(BaseModel):
    """Запрос на создание платежа"""
    user_id: str
    amount: float
    description: Optional[str] = None


class PaymentResponse(BaseModel):
    """Ответ для платежа"""
    success: bool
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
    status: str
    processing_time: float
    timestamp: str
    error: Optional[str] = None


class PaymentInfo(BaseModel):
    """Информация о платеже"""
    id: str
    user_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SubscriptionInfo(BaseModel):
    """Информация о подписке"""
    id: str
    user_id: str
    plan_type: str
    status: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    created_at: str
    updated_at: str
    is_active: bool


class StatisticsResponse(BaseModel):
    """Ответ со статистикой"""
    total_payments: int
    completed_payments: int
    failed_payments: int
    pending_payments: int
    total_revenue: float
    total_subscriptions: int
    active_subscriptions: int
    unique_users: int


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global payment_service
    
    try:
        logger.info("🚀 Инициализация Payment Service...")
        
        payment_repository = InMemoryPaymentRepository()
        
        payment_service = PaymentService(payment_repository)
        
        logger.info("✅ Payment Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Payment Service: {e}")
        raise


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        if payment_service is None:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        stats = payment_service.get_statistics()
        
        return {
            "status": "healthy",
            "service": "payment",
            "timestamp": datetime.now().isoformat(),
            "total_payments": stats["total_payments"],
            "active_subscriptions": stats["active_subscriptions"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.post("/create-payment", response_model=PaymentResponse)
async def create_payment(request: CreatePaymentRequest):
    """Создать платеж"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Создаем платеж для пользователя: {request.user_id}")
        
        payment = payment_service.create_payment(
            user_id=request.user_id,
            amount=request.amount,
            description=request.description
        )
        
        processing_time = time.time() - start_time
        
        return PaymentResponse(
            success=True,
            payment_id=payment.id,
            status="created",
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Ошибка создания платежа: {e}")
        
        return PaymentResponse(
            success=False,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@app.post("/process-payment/{payment_id}", response_model=PaymentResponse)
async def process_payment(payment_id: str):
    """Обработать платеж"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Обрабатываем платеж: {payment_id}")
        
        result = payment_service.process_payment(payment_id)
        
        processing_time = time.time() - start_time
        
        return PaymentResponse(
            success=result["success"],
            payment_id=result["payment_id"],
            subscription_id=result.get("subscription_id"),
            status=result["status"],
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=result.get("error")
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Ошибка обработки платежа: {e}")
        
        return PaymentResponse(
            success=False,
            payment_id=payment_id,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )


@app.get("/payment/{payment_id}", response_model=PaymentInfo)
async def get_payment(payment_id: str):
    """Получить платеж по ID"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        payment = payment_service.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return PaymentInfo(
            id=payment.id,
            user_id=payment.user_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            payment_method=payment.payment_method,
            description=payment.description,
            created_at=payment.created_at.isoformat(),
            updated_at=payment.updated_at.isoformat(),
            completed_at=payment.completed_at.isoformat() if payment.completed_at else None,
            metadata=payment.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения платежа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/payments")
async def get_user_payments(user_id: str, limit: int = 10):
    """Получить платежи пользователя"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        payments = payment_service.get_user_payments(user_id, limit)
        
        result = []
        for payment in payments:
            result.append({
                "id": payment.id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "created_at": payment.created_at.isoformat(),
                "updated_at": payment.updated_at.isoformat()
            })
        
        return {
            "user_id": user_id,
            "payments": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения платежей пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/subscription")
async def get_user_subscription(user_id: str):
    """Получить подписку пользователя"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        subscription_status = payment_service.check_subscription_status(user_id)
        
        return subscription_status
        
    except Exception as e:
        logger.error(f"Ошибка получения подписки пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/subscription/{subscription_id}", response_model=SubscriptionInfo)
async def get_subscription(subscription_id: str):
    """Получить подписку по ID"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        subscription = payment_service.get_subscription(subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return SubscriptionInfo(
            id=subscription.id,
            user_id=subscription.user_id,
            plan_type=subscription.plan_type,
            status=subscription.status,
            start_date=subscription.start_date.isoformat() if subscription.start_date else None,
            end_date=subscription.end_date.isoformat() if subscription.end_date else None,
            created_at=subscription.created_at.isoformat(),
            updated_at=subscription.updated_at.isoformat(),
            is_active=subscription.is_active()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения подписки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/subscription/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str):
    """Отменить подписку"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        success = payment_service.cancel_subscription(subscription_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return {
            "success": True,
            "subscription_id": subscription_id,
            "message": "Subscription cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отмены подписки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Получить статистику"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        stats = payment_service.get_statistics()
        
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/payment/{payment_id}")
async def delete_payment(payment_id: str):
    """Удалить платеж"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        success = payment_service.delete_payment(payment_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return {
            "success": True,
            "payment_id": payment_id,
            "message": "Payment deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления платежа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/subscription/{subscription_id}")
async def delete_subscription(subscription_id: str):
    """Удалить подписку"""
    try:
        if payment_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        success = payment_service.delete_subscription(subscription_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return {
            "success": True,
            "subscription_id": subscription_id,
            "message": "Subscription deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления подписки: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
