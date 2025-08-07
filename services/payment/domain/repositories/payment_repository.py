"""
Репозиторий для работы с платежами в Payment Service
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.payment import Payment, Subscription


class PaymentRepository(ABC):
    """Абстрактный репозиторий для работы с платежами"""
    
    @abstractmethod
    def save_payment(self, payment: Payment) -> str:
        """Сохранить платеж"""
        pass
    
    @abstractmethod
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Получить платеж по ID"""
        pass
    
    @abstractmethod
    def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Обновить статус платежа"""
        pass
    
    @abstractmethod
    def get_user_payments(self, user_id: str, limit: int = 10) -> List[Payment]:
        """Получить платежи пользователя"""
        pass
    
    @abstractmethod
    def save_subscription(self, subscription: Subscription) -> str:
        """Сохранить подписку"""
        pass
    
    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Получить подписку по ID"""
        pass
    
    @abstractmethod
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Получить подписку пользователя"""
        pass
    
    @abstractmethod
    def update_subscription_status(self, subscription_id: str, status: str) -> bool:
        """Обновить статус подписки"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        pass
    
    @abstractmethod
    def delete_payment(self, payment_id: str) -> bool:
        """Удалить платеж"""
        pass
    
    @abstractmethod
    def delete_subscription(self, subscription_id: str) -> bool:
        """Удалить подписку"""
        pass
