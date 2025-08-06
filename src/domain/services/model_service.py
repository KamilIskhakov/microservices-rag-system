"""
Доменный сервис для работы с моделями
"""
from typing import List, Optional, Dict, Any
from src.domain.entities.model import Model
from src.domain.repositories.model_repository import ModelRepository


class ModelService:
    """Доменный сервис для работы с моделями"""
    
    def __init__(self, model_repository: ModelRepository):
        self.model_repository = model_repository
    
    def load_model(self, model_id: str, device: str = "auto") -> Model:
        """Загрузить модель"""
        model = self.model_repository.load_model(model_id, device)
        return model
    
    def unload_model(self, model_id: str) -> bool:
        """Выгрузить модель"""
        return self.model_repository.unload_model(model_id)
    
    def get_loaded_models(self) -> List[Model]:
        """Получить все загруженные модели"""
        return self.model_repository.find_loaded_models()
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о модели"""
        return self.model_repository.get_model_info(model_id)
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Получить информацию об использовании памяти"""
        return self.model_repository.get_memory_usage()
    
    def optimize_memory(self) -> None:
        """Оптимизировать память"""
        self.model_repository.optimize_memory()
    
    def is_model_available(self, model_id: str) -> bool:
        """Проверить доступность модели"""
        model = self.model_repository.find_by_id(model_id)
        return model is not None and model.is_available() 