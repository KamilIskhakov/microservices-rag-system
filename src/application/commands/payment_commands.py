"""
Команды для работы с платежами
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

from src.domain.repositories.payment_repository import PaymentRepository
from src.domain.entities.payment import Payment, Subscription
from src.application.commands.command_bus import CommandBus

@dataclass
class CreatePaymentCommand:
    """Команда создания платежа"""
    user_id: str
    amount: float
    currency: str = "RUB"
    description: str = ""
    payment_method: str = "yookassa"

@dataclass
class CreatePaymentResult:
    """Результат создания платежа"""
    payment_id: str
    payment_url: str
    status: str = "pending"

@dataclass
class ProcessPaymentCommand:
    """Команда обработки платежа"""
    payment_id: str

@dataclass
class ProcessPaymentResult:
    """Результат обработки платежа"""
    payment_id: str
    status: str

class CreatePaymentCommandHandler:
    """Обработчик команды создания платежа"""
    
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
    
    async def handle(self, command: CreatePaymentCommand) -> CreatePaymentResult:
        """Обработка команды создания платежа"""
        # Создаем платеж
        payment = Payment(
            payment_id=None,  # Будет сгенерирован автоматически
            user_id=command.user_id,
            amount=command.amount,
            currency=command.currency,
            status="pending",
            payment_method=command.payment_method,
            description=command.description
        )
        
        # Сохраняем платеж
        payment_id = self.payment_repository.save_payment(payment)
        
        # Генерируем URL для оплаты (заглушка)
        payment_url = f"https://yookassa.ru/pay/{payment_id}"
        
        return CreatePaymentResult(
            payment_id=payment_id,
            payment_url=payment_url,
            status="pending"
        )

class ProcessPaymentCommandHandler:
    """Обработчик команды обработки платежа"""
    
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
    
    async def handle(self, command: ProcessPaymentCommand) -> ProcessPaymentResult:
        """Обработка команды обработки платежа"""
        # Получаем платеж
        payment = self.payment_repository.get_payment(command.payment_id)
        
        if not payment:
            raise ValueError(f"Payment {command.payment_id} not found")
        
        # Обновляем статус платежа (заглушка)
        self.payment_repository.update_payment_status(command.payment_id, "completed")
        
        return ProcessPaymentResult(
            payment_id=command.payment_id,
            status="completed"
        ) 