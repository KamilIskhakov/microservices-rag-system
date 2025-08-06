"""
Репозиторий для платежей
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.entities.payment import Payment, Subscription

class PaymentRepository(ABC):
    """Абстрактный репозиторий для платежей"""
    
    @abstractmethod
    def save_payment(self, payment: Payment) -> str:
        """Сохранение платежа"""
        pass
    
    @abstractmethod
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Получение платежа по ID"""
        pass
    
    @abstractmethod
    def get_user_payments(self, user_id: str) -> List[Payment]:
        """Получение платежей пользователя"""
        pass
    
    @abstractmethod
    def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Обновление статуса платежа"""
        pass
    
    @abstractmethod
    def save_subscription(self, subscription: Subscription) -> str:
        """Сохранение подписки"""
        pass
    
    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Получение подписки по ID"""
        pass
    
    @abstractmethod
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Получение активной подписки пользователя"""
        pass
    
    @abstractmethod
    def update_subscription_status(self, subscription_id: str, status: str) -> bool:
        """Обновление статуса подписки"""
        pass

class InMemoryPaymentRepository(PaymentRepository):
    """In-memory реализация репозитория платежей"""
    
    def __init__(self):
        self.payments: Dict[str, Payment] = {}
        self.subscriptions: Dict[str, Subscription] = {}
    
    def save_payment(self, payment: Payment) -> str:
        """Сохранение платежа"""
        self.payments[payment.payment_id] = payment
        return payment.payment_id
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Получение платежа по ID"""
        return self.payments.get(payment_id)
    
    def get_user_payments(self, user_id: str) -> List[Payment]:
        """Получение платежей пользователя"""
        return [
            payment for payment in self.payments.values()
            if payment.user_id == user_id
        ]
    
    def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Обновление статуса платежа"""
        if payment_id in self.payments:
            self.payments[payment_id].status = status
            if status == "completed":
                self.payments[payment_id].completed_at = datetime.now()
            return True
        return False
    
    def save_subscription(self, subscription: Subscription) -> str:
        """Сохранение подписки"""
        self.subscriptions[subscription.subscription_id] = subscription
        return subscription.subscription_id
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Получение подписки по ID"""
        return self.subscriptions.get(subscription_id)
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Получение активной подписки пользователя"""
        for subscription in self.subscriptions.values():
            if subscription.user_id == user_id and subscription.is_active:
                return subscription
        return None
    
    def update_subscription_status(self, subscription_id: str, status: str) -> bool:
        """Обновление статуса подписки"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].status = status
            return True
        return False 