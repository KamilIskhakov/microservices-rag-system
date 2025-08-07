"""
Доменная сущность ScrapedData для Scraper Service
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


@dataclass
class ScrapedData:
    """Доменная сущность скрапленных данных"""
    id: str
    source_url: str
    content: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "pending"
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def mark_processed(self) -> None:
        """Отметить как обработанные"""
        self.status = "processed"
        self.updated_at = datetime.now()
    
    def mark_failed(self, error: str) -> None:
        """Отметить как неудачные"""
        self.status = "failed"
        self.error = error
        self.updated_at = datetime.now()
    
    def update_content(self, content: str) -> None:
        """Обновить содержимое"""
        self.content = content
        self.updated_at = datetime.now()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Обновить метаданные"""
        self.metadata = metadata
        self.updated_at = datetime.now()


@dataclass
class ScrapingJob:
    """Доменная сущность задачи скрапинга"""
    id: str
    source_url: str
    job_type: str = "minjust"
    status: str = "pending"
    priority: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def start(self) -> None:
        """Начать выполнение"""
        self.status = "running"
        self.started_at = datetime.now()
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Завершить выполнение"""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def fail(self, error: str) -> None:
        """Отметить как неудачное"""
        self.status = "failed"
        self.error = error
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def cancel(self) -> None:
        """Отменить задачу"""
        self.status = "cancelled"
        self.updated_at = datetime.now()
