"""
Сущность для векторных документов
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

@dataclass
class VectorDocument:
    """Векторный документ"""
    id: str
    text: str
    embedding: Optional[List[float]] = None
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
class SearchResult:
    """Результат поиска"""
    document: VectorDocument
    relevance_score: float
    rank: int = 0
    
    @property
    def text(self) -> str:
        return self.document.text
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self.document.metadata 