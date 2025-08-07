"""
Доменная сущность Model для AI Model Service
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Model:
    """Доменная сущность модели AI"""
    id: str
    name: str
    type: str
    device: str
    is_loaded: bool
    path: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def load(self) -> None:
        """Загрузить модель"""
        self.is_loaded = True
        self.updated_at = datetime.now()
    
    def unload(self) -> None:
        """Выгрузить модель"""
        self.is_loaded = False
        self.updated_at = datetime.now()
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Обновить метаданные модели"""
        self.metadata = metadata
        self.updated_at = datetime.now()
    
    def is_available(self) -> bool:
        """Проверить доступность модели"""
        return self.is_loaded
