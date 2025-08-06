"""
Сущности для платежей и подписок
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

@dataclass
class Payment:
    """Платеж"""
    payment_id: str
    user_id: str
    amount: float
    currency: str
    status: str  # "pending", "completed", "failed", "cancelled"
    payment_method: str
    description: str = ""
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.payment_id is None:
            self.payment_id = str(uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Subscription:
    """Подписка"""
    subscription_id: str
    user_id: str
    plan_type: str  # "basic", "premium", "enterprise"
    start_date: datetime
    end_date: datetime
    status: str  # "active", "expired", "cancelled"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.subscription_id is None:
            self.subscription_id = str(uuid4())
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_active(self) -> bool:
        """Проверка активности подписки"""
        now = datetime.now()
        return (
            self.status == "active" and 
            self.start_date <= now <= self.end_date
        )
    
    @property
    def days_remaining(self) -> int:
        """Количество оставшихся дней"""
        if not self.is_active:
            return 0
        delta = self.end_date - datetime.now()
        return max(0, delta.days) 