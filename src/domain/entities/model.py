"""
Доменная сущность Model
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


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