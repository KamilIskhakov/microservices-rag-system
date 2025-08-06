"""
Сущность для данных, полученных через парсинг
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

@dataclass
class ScrapedData:
    """Данные, полученные через парсинг"""
    id: str
    number: str  # Номер материала
    content: str  # Содержимое материала
    date: datetime  # Дата внесения
    source: str = "minjust"
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ScrapingJob:
    """Задача парсинга"""
    job_id: str
    source: str
    status: str  # "pending", "running", "completed", "failed", "cancelled"
    progress: float = 0.0
    items_processed: int = 0
    items_total: int = 0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.job_id is None:
            self.job_id = str(uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def duration(self) -> Optional[float]:
        """Длительность выполнения в секундах"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None 