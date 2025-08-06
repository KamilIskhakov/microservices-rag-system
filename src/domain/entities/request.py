"""
Доменная сущность Request
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RequestStatus(Enum):
    """Статусы запроса"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RequestType(Enum):
    """Типы запросов"""
    CHECK_EXTREMISM = "check_extremism"
    GENERATE_RESPONSE = "generate_response"
    SEARCH_CONTEXT = "search_context"


@dataclass
class Request:
    """Доменная сущность запроса"""
    
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    id: Optional[str] = None
    request_type: RequestType = RequestType.CHECK_EXTREMISM
    status: RequestStatus = RequestStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    context: Optional[List[str]] = None
    result: Optional[str] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    
    def __post_init__(self):
        """Инициализация после создания объекта"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def start_processing(self) -> None:
        """Начать обработку запроса"""
        self.status = RequestStatus.PROCESSING
        self.updated_at = datetime.now()
    
    def complete(self, result: str, processing_time: float) -> None:
        """Завершить обработку запроса"""
        self.status = RequestStatus.COMPLETED
        self.result = result
        self.processing_time = processing_time
        self.updated_at = datetime.now()
    
    def fail(self, error: str) -> None:
        """Завершить запрос с ошибкой"""
        self.status = RequestStatus.FAILED
        self.error = error
        self.updated_at = datetime.now()
    
    def add_context(self, context: List[str]) -> None:
        """Добавить контекст к запросу"""
        self.context = context
        self.updated_at = datetime.now()
    
    def get_info(self) -> dict:
        """Получить информацию о запросе"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "query": self.query,
            "request_type": self.request_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "context_count": len(self.context) if self.context else 0,
            "result": self.result,
            "error": self.error,
            "processing_time": self.processing_time
        } 