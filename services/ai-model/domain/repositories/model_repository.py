"""
Репозиторий для работы с моделями в AI Model Service
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.model import Model


class ModelRepository(ABC):
    """Абстрактный репозиторий для работы с моделями"""
    
    @abstractmethod
    def save(self, model: Model) -> Model:
        """Сохранить модель"""
        pass
    
    @abstractmethod
    def find_by_id(self, model_id: str) -> Optional[Model]:
        """Найти модель по ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Model]:
        """Найти все модели"""
        pass
    
    @abstractmethod
    def find_loaded_models(self) -> List[Model]:
        """Найти все загруженные модели"""
        pass
    
    @abstractmethod
    def delete(self, model_id: str) -> bool:
        """Удалить модель"""
        pass
    
    @abstractmethod
    def load_model(self, model_id: str, device: str = "auto") -> Model:
        """Загрузить модель в память"""
        pass
    
    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Выгрузить модель из памяти"""
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> Dict[str, Any]:
        """Получить информацию об использовании памяти"""
        pass
    
    @abstractmethod
    def optimize_memory(self) -> None:
        """Оптимизировать использование памяти"""
        pass
    
    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о модели"""
        pass
