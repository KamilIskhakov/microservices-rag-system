"""
Базовый интерфейс для репозиториев
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Базовый интерфейс для репозиториев"""
    
    @abstractmethod
    def save(self, entity: T) -> str:
        """Сохраняет сущность"""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Получает сущность по ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Получает все сущности"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Удаляет сущность"""
        pass
    
    @abstractmethod
    def update(self, entity_id: str, entity: T) -> bool:
        """Обновляет сущность"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику репозитория"""
        pass 