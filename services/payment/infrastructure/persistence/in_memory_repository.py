"""
In-Memory реализация репозитория для Payment Service
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from domain.repositories.payment_repository import PaymentRepository
from domain.entities.payment import Payment, Subscription

logger = logging.getLogger(__name__)


class InMemoryPaymentRepository(PaymentRepository):
    """In-Memory реализация репозитория платежей"""
    
    def __init__(self):
        self.payments: Dict[str, Payment] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.user_payments: Dict[str, List[str]] = defaultdict(list)
        self.user_subscriptions: Dict[str, str] = {}  # user_id -> subscription_id
        self._payment_count = 0
        self._subscription_count = 0
    
    def save_payment(self, payment: Payment) -> str:
        """Сохранить платеж"""
        payment_id = str(payment.id)
        self.payments[payment_id] = payment
        
        if payment.user_id:
            self.user_payments[payment.user_id].append(payment_id)
        
        self._payment_count += 1
        logger.info(f"Платеж сохранен: {payment_id}")
        return payment_id
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Получить платеж по ID"""
        return self.payments.get(payment_id)
    
    def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Обновить статус платежа"""
        if payment_id in self.payments:
            self.payments[payment_id].status = status
            self.payments[payment_id].updated_at = datetime.now()
            logger.info(f"Статус платежа {payment_id} обновлен: {status}")
            return True
        return False
    
    def get_user_payments(self, user_id: str, limit: int = 10) -> List[Payment]:
        """Получить платежи пользователя"""
        if user_id not in self.user_payments:
            return []
        
        payment_ids = self.user_payments[user_id][-limit:]
        return [self.payments[pay_id] for pay_id in payment_ids if pay_id in self.payments]
    
    def save_subscription(self, subscription: Subscription) -> str:
        """Сохранить подписку"""
        subscription_id = str(subscription.id)
        self.subscriptions[subscription_id] = subscription
        
        if subscription.user_id:
            self.user_subscriptions[subscription.user_id] = subscription_id
        
        self._subscription_count += 1
        logger.info(f"Подписка сохранена: {subscription_id}")
        return subscription_id
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Получить подписку по ID"""
        return self.subscriptions.get(subscription_id)
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Получить подписку пользователя"""
        if user_id not in self.user_subscriptions:
            return None
        
        subscription_id = self.user_subscriptions[user_id]
        return self.subscriptions.get(subscription_id)
    
    def update_subscription_status(self, subscription_id: str, status: str) -> bool:
        """Обновить статус подписки"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].status = status
            self.subscriptions[subscription_id].updated_at = datetime.now()
            logger.info(f"Статус подписки {subscription_id} обновлен: {status}")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        total_payments = len(self.payments)
        completed_payments = len([p for p in self.payments.values() if p.status == "completed"])
        failed_payments = len([p for p in self.payments.values() if p.status == "failed"])
        pending_payments = len([p for p in self.payments.values() if p.status == "pending"])
        
        total_revenue = sum([p.amount for p in self.payments.values() if p.status == "completed"])
        
        total_subscriptions = len(self.subscriptions)
        active_subscriptions = len([s for s in self.subscriptions.values() if s.is_active()])
        
        return {
            "total_payments": total_payments,
            "completed_payments": completed_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "total_revenue": total_revenue,
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "unique_users": len(self.user_payments)
        }
    
    def delete_payment(self, payment_id: str) -> bool:
        """Удалить платеж"""
        if payment_id in self.payments:
            payment = self.payments[payment_id]
            
            if payment.user_id and payment_id in self.user_payments[payment.user_id]:
                self.user_payments[payment.user_id].remove(payment_id)
            
            del self.payments[payment_id]
            
            logger.info(f"Платеж удален: {payment_id}")
            return True
        return False
    
    def delete_subscription(self, subscription_id: str) -> bool:
        """Удалить подписку"""
        if subscription_id in self.subscriptions:
            subscription = self.subscriptions[subscription_id]
            
            if subscription.user_id and subscription.user_id in self.user_subscriptions:
                del self.user_subscriptions[subscription.user_id]
            
            del self.subscriptions[subscription_id]
            
            logger.info(f"Подписка удалена: {subscription_id}")
            return True
        return False
