"""
Репозиторий для работы с запросами в Request Processor Service
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.request import Request


class RequestRepository(ABC):
    """Абстрактный репозиторий для работы с запросами"""
    
    @abstractmethod
    def save_request(self, request: Request) -> str:
        """Сохранить запрос"""
        pass
    
    @abstractmethod
    def get_request(self, request_id: str) -> Optional[Request]:
        """Получить запрос по ID"""
        pass
    
    @abstractmethod
    def update_request_status(self, request_id: str, status: str) -> bool:
        """Обновить статус запроса"""
        pass
    
    @abstractmethod
    def update_request_results(self, request_id: str, results: Dict[str, Any]) -> bool:
        """Обновить результаты запроса"""
        pass
    
    @abstractmethod
    def get_user_requests(self, user_id: str, limit: int = 10) -> List[Request]:
        """Получить запросы пользователя"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        pass
    
    @abstractmethod
    def delete_request(self, request_id: str) -> bool:
        """Удалить запрос"""
        pass
    
    @abstractmethod
    def get_pending_requests(self) -> List[Request]:
        """Получить ожидающие запросы"""
        pass
