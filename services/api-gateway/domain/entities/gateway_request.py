"""
Доменная сущность GatewayRequest для API Gateway Service
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


@dataclass
class GatewayRequest:
    """Доменная сущность запроса к API Gateway"""
    id: str
    method: str
    path: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    status_code: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def set_response(self, status_code: int, response_body: Dict[str, Any]) -> None:
        """Установить ответ"""
        self.status_code = status_code
        self.response_body = response_body
    
    def set_error(self, error: str) -> None:
        """Установить ошибку"""
        self.error = error
    
    def set_processing_time(self, processing_time: float) -> None:
        """Установить время обработки"""
        self.processing_time = processing_time


@dataclass
class ServiceEndpoint:
    """Доменная сущность эндпоинта сервиса"""
    name: str
    url: str
    health_check_path: str = "/health"
    is_available: bool = True
    last_check: Optional[datetime] = None
    response_time: Optional[float] = None
    
    def update_health(self, is_available: bool, response_time: float = None) -> None:
        """Обновить состояние здоровья"""
        self.is_available = is_available
        self.last_check = datetime.now()
        if response_time:
            self.response_time = response_time
