"""
Доменный сервис для работы с платежами в Payment Service
"""
import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..entities.payment import Payment, Subscription
from ..repositories.payment_repository import PaymentRepository

logger = logging.getLogger(__name__)


class PaymentService:
    """Доменный сервис для работы с платежами"""
    
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
        self.shop_id = os.getenv("YOOKASSA_SHOP_ID", "")
        self.secret_key = os.getenv("YOOKASSA_SECRET_KEY", "")
    
    def create_payment(self, user_id: str, amount: float, description: str = None) -> Payment:
        """Создать платеж"""
        payment = Payment(
            id=None,
            user_id=user_id,
            amount=amount,
            description=description or f"Платеж пользователя {user_id}"
        )
        
        payment_id = self.payment_repository.save_payment(payment)
        logger.info(f"Создан платеж: {payment_id} для пользователя {user_id}")
        
        return payment
    
    def process_payment(self, payment_id: str) -> Dict[str, Any]:
        """Обработать платеж"""
        payment = self.payment_repository.get_payment(payment_id)
        if not payment:
            raise ValueError(f"Платеж {payment_id} не найден")
        
        try:
            # Имитация обработки платежа через YooKassa
            if self._process_yookassa_payment(payment):
                payment.complete()
                self.payment_repository.update_payment_status(payment_id, "completed")
                
                # Создаем подписку при успешном платеже
                subscription = self._create_subscription_for_payment(payment)
                
                return {
                    "success": True,
                    "payment_id": payment_id,
                    "subscription_id": subscription.id,
                    "status": "completed"
                }
            else:
                payment.fail("Ошибка обработки платежа")
                self.payment_repository.update_payment_status(payment_id, "failed")
                
                return {
                    "success": False,
                    "payment_id": payment_id,
                    "status": "failed",
                    "error": "Payment processing failed"
                }
                
        except Exception as e:
            payment.fail(str(e))
            self.payment_repository.update_payment_status(payment_id, "failed")
            logger.error(f"Ошибка обработки платежа {payment_id}: {e}")
            
            return {
                "success": False,
                "payment_id": payment_id,
                "status": "failed",
                "error": str(e)
            }
    
    def _process_yookassa_payment(self, payment: Payment) -> bool:
        """Обработать платеж через YooKassa (имитация)"""
        # В реальном проекте здесь был бы вызов API YooKassa
        # Сейчас просто имитируем успешную обработку
        logger.info(f"Обрабатываем платеж через YooKassa: {payment.id}")
        
        # Проверяем наличие конфигурации
        if not self.shop_id or not self.secret_key:
            logger.warning("YooKassa конфигурация не настроена")
            return False
        
        # Имитируем успешную обработку
        return True
    
    def _create_subscription_for_payment(self, payment: Payment) -> Subscription:
        """Создать подписку для платежа"""
        # Определяем тип подписки по сумме
        plan_type = self._determine_plan_type(payment.amount)
        
        subscription = Subscription(
            id=None,
            user_id=payment.user_id,
            plan_type=plan_type,
            status="active",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),  # 30 дней
            metadata={
                "payment_id": payment.id,
                "amount": payment.amount
            }
        )
        
        subscription_id = self.payment_repository.save_subscription(subscription)
        logger.info(f"Создана подписка: {subscription_id} для пользователя {payment.user_id}")
        
        return subscription
    
    def _determine_plan_type(self, amount: float) -> str:
        """Определить тип плана по сумме"""
        if amount >= 1000:
            return "premium"
        elif amount >= 500:
            return "standard"
        else:
            return "basic"
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Получить подписку пользователя"""
        return self.payment_repository.get_user_subscription(user_id)
    
    def check_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Проверить статус подписки пользователя"""
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            return {
                "has_subscription": False,
                "status": "no_subscription",
                "plan_type": None,
                "is_active": False
            }
        
        return {
            "has_subscription": True,
            "status": subscription.status,
            "plan_type": subscription.plan_type,
            "is_active": subscription.is_active(),
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None
        }
    
    def get_user_payments(self, user_id: str, limit: int = 10) -> List[Payment]:
        """Получить платежи пользователя"""
        return self.payment_repository.get_user_payments(user_id, limit)
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Получить платеж по ID"""
        return self.payment_repository.get_payment(payment_id)
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Получить подписку по ID"""
        return self.payment_repository.get_subscription(subscription_id)
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """Отменить подписку"""
        subscription = self.payment_repository.get_subscription(subscription_id)
        if not subscription:
            return False
        
        subscription.deactivate()
        return self.payment_repository.update_subscription_status(subscription_id, "inactive")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        return self.payment_repository.get_statistics()
    
    def delete_payment(self, payment_id: str) -> bool:
        """Удалить платеж"""
        return self.payment_repository.delete_payment(payment_id)
    
    def delete_subscription(self, subscription_id: str) -> bool:
        """Удалить подписку"""
        return self.payment_repository.delete_subscription(subscription_id)
