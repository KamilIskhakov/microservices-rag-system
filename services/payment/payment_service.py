"""
Payment Service - обработка платежей и подписок
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.domain.entities.payment import Payment, Subscription
from src.infrastructure.persistence.in_memory_repositories import InMemoryPaymentRepository as PaymentRepository
from src.application.commands.payment_commands import (
    CreatePaymentCommand,
    CreatePaymentCommandHandler,
    ProcessPaymentCommand,
    ProcessPaymentCommandHandler,
    CommandBus
)
from src.shared.utils.logger import logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logger

app = FastAPI(title="RAG Payment Service", version="2.0.0")

# Подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Глобальные переменные
payment_repository: Optional[PaymentRepository] = None
command_bus: Optional[CommandBus] = None

class PaymentRequest(BaseModel):
    """Запрос на создание платежа"""
    user_id: str
    amount: float
    currency: str = "RUB"
    description: str = ""
    payment_method: str = "yookassa"

class PaymentResponse(BaseModel):
    """Ответ на создание платежа"""
    success: bool
    payment_id: Optional[str] = None
    payment_url: Optional[str] = None
    amount: float = 0.0
    currency: str = "RUB"
    status: str = "pending"
    timestamp: str
    error: Optional[str] = None

class SubscriptionRequest(BaseModel):
    """Запрос на создание подписки"""
    user_id: str
    plan_type: str  # "basic", "premium", "enterprise"
    duration_days: int = 30

class SubscriptionResponse(BaseModel):
    """Ответ на создание подписки"""
    success: bool
    subscription_id: Optional[str] = None
    plan_type: str = ""
    start_date: str = ""
    end_date: str = ""
    status: str = "active"
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
    global payment_repository, command_bus
    
    try:
        logger.info("🚀 Инициализация Payment Service...")
        
        # Инициализируем репозиторий платежей
        payment_repository = PaymentRepository()
        
        # Инициализируем шину команд
        command_bus = CommandBus()
        
        # Регистрируем обработчики команд
        command_bus.register_handler(
            CreatePaymentCommand,
            CreatePaymentCommandHandler(payment_repository)
        )
        
        command_bus.register_handler(
            ProcessPaymentCommand,
            ProcessPaymentCommandHandler(payment_repository)
        )
        
        logger.info("✅ Payment Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Payment Service: {e}")
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
            "yookassa": "unknown"  # Будет проверяться через API
        }
        
        return HealthResponse(
            status="healthy" if redis_healthy == "healthy" else "unhealthy",
            service="payment",
            timestamp=datetime.now().isoformat(),
            dependencies=dependencies
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="payment",
            timestamp=datetime.now().isoformat(),
            dependencies={"error": str(e)}
        )

@app.post("/create-payment", response_model=PaymentResponse)
async def create_payment(request: PaymentRequest):
    """Создание нового платежа"""
    start_time = time.time()
    
    try:
        logger.info(f"💰 Создание платежа для пользователя {request.user_id}")
        
        # Создаем команду для создания платежа
        command = CreatePaymentCommand(
            user_id=request.user_id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            payment_method=request.payment_method
        )
        
        # Отправляем команду через шину команд
        result = await command_bus.handle(command)
        
        return PaymentResponse(
            success=True,
            payment_id=result.payment_id,
            payment_url=result.payment_url,
            amount=request.amount,
            currency=request.currency,
            status="pending",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        
        return PaymentResponse(
            success=False,
            amount=request.amount,
            currency=request.currency,
            status="failed",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@app.post("/process-payment/{payment_id}")
async def process_payment(payment_id: str):
    """Обработка платежа (webhook от платежной системы)"""
    try:
        logger.info(f"💳 Обработка платежа {payment_id}")
        
        # Создаем команду для обработки платежа
        command = ProcessPaymentCommand(payment_id=payment_id)
        
        # Отправляем команду через шину команд
        result = await command_bus.handle(command)
        
        return {
            "success": True,
            "payment_id": payment_id,
            "status": result.status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки платежа {payment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(request: SubscriptionRequest):
    """Создание подписки"""
    try:
        logger.info(f"📅 Создание подписки для пользователя {request.user_id}")
        
        # Создаем подписку
        subscription = Subscription(
            user_id=request.user_id,
            plan_type=request.plan_type,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=request.duration_days),
            status="active"
        )
        
        # Сохраняем в репозитории
        subscription_id = payment_repository.save_subscription(subscription)
        
        return SubscriptionResponse(
            success=True,
            subscription_id=subscription_id,
            plan_type=request.plan_type,
            start_date=subscription.start_date.isoformat(),
            end_date=subscription.end_date.isoformat(),
            status="active",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания подписки: {e}")
        
        return SubscriptionResponse(
            success=False,
            plan_type=request.plan_type,
            status="failed",
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@app.get("/subscription/{user_id}")
async def get_user_subscription(user_id: str):
    """Получение подписки пользователя"""
    try:
        subscription = payment_repository.get_user_subscription(user_id)
        
        if subscription is None:
            return {
                "success": False,
                "message": "Подписка не найдена"
            }
        
        return {
            "success": True,
            "subscription": {
                "user_id": subscription.user_id,
                "plan_type": subscription.plan_type,
                "start_date": subscription.start_date.isoformat(),
                "end_date": subscription.end_date.isoformat(),
                "status": subscription.status
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting subscription for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payments/{user_id}")
async def get_user_payments(user_id: str):
    """Получение платежей пользователя"""
    try:
        payments = payment_repository.get_user_payments(user_id)
        
        return {
            "success": True,
            "payments": [
                {
                    "payment_id": payment.payment_id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status,
                    "created_at": payment.created_at.isoformat()
                }
                for payment in payments
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting payments for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004) 