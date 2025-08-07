"""
Доменная сущность Payment для Payment Service
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Payment:
    """Доменная сущность платежа"""
    id: str
    user_id: str
    amount: float
    currency: str = "RUB"
    status: str = "pending"
    payment_method: str = "yookassa"
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Завершить платеж"""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def fail(self, reason: str) -> None:
        """Отметить платеж как неудачный"""
        self.status = "failed"
        self.metadata = self.metadata or {}
        self.metadata["failure_reason"] = reason
        self.updated_at = datetime.now()
    
    def cancel(self) -> None:
        """Отменить платеж"""
        self.status = "cancelled"
        self.updated_at = datetime.now()


@dataclass
class Subscription:
    """Доменная сущность подписки"""
    id: str
    user_id: str
    plan_type: str
    status: str = "active"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Активировать подписку"""
        self.status = "active"
        self.start_date = datetime.now()
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Деактивировать подписку"""
        self.status = "inactive"
        self.end_date = datetime.now()
        self.updated_at = datetime.now()
    
    def is_active(self) -> bool:
        """Проверить активность подписки"""
        if self.status != "active":
            return False
        if self.end_date and datetime.now() > self.end_date:
            return False
        return True
