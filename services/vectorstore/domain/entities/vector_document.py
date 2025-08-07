"""
Доменная сущность VectorDocument для Vector Store Service
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


@dataclass
class VectorDocument:
    """Доменная сущность векторного документа"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def update_embedding(self, embedding: List[float]) -> None:
        """Обновить эмбеддинг документа"""
        self.embedding = embedding
        self.updated_at = datetime.now()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Обновить метаданные документа"""
        self.metadata.update(metadata)
        self.updated_at = datetime.now()
    
    def is_indexed(self) -> bool:
        """Проверить, индексирован ли документ"""
        return self.embedding is not None


@dataclass
class SearchResult:
    """Результат поиска"""
    document_id: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any]
    distance: Optional[float] = None
    
    def __post_init__(self):
        if self.distance is None:
            self.distance = 1.0 - self.relevance_score
