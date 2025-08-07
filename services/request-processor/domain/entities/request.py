"""
Доменная сущность Request для Request Processor Service
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


@dataclass
class Request:
    """Доменная сущность запроса"""
    id: str
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def update_status(self, status: str) -> None:
        """Обновить статус запроса"""
        self.status = status
        self.updated_at = datetime.now()
    
    def set_results(self, results: Dict[str, Any]) -> None:
        """Установить результаты обработки"""
        self.results = results
        self.status = "completed"
        self.updated_at = datetime.now()
    
    def set_error(self, error: str) -> None:
        """Установить ошибку"""
        self.error = error
        self.status = "failed"
        self.updated_at = datetime.now()
    
    def set_processing_time(self, processing_time: float) -> None:
        """Установить время обработки"""
        self.processing_time = processing_time
