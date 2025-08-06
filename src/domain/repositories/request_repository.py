"""
Репозиторий для работы с запросами
"""
from abc import abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from src.domain.entities.request import Request
from src.domain.repositories.base_repository import BaseRepository

class RequestRepository(BaseRepository[Request]):
    """Абстрактный репозиторий для работы с запросами"""
    
    @abstractmethod
    def save_request(self, request: Request) -> str:
        """Сохранение запроса"""
        pass
    
    @abstractmethod
    def get_request(self, request_id: str) -> Optional[Request]:
        """Получение запроса по ID"""
        pass
    
    @abstractmethod
    def update_request_status(self, request_id: str, status: str) -> bool:
        """Обновление статуса запроса"""
        pass
    
    @abstractmethod
    def get_user_requests(self, user_id: str, limit: int = 10) -> List[Request]:
        """Получение запросов пользователя"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Request]:
        """Получение всех запросов"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Удаление запроса"""
        pass
    
    @abstractmethod
    def update(self, entity_id: str, entity: Request) -> bool:
        """Обновление запроса"""
        pass
    
    @abstractmethod
    def save(self, entity: Request) -> str:
        """Сохранение запроса (алиас для save_request)"""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Request]:
        """Получение запроса по ID (алиас для get_request)"""
        pass

class InMemoryRequestRepository(RequestRepository):
    """In-memory реализация репозитория запросов"""
    
    def __init__(self):
        self._requests: Dict[str, Request] = {}
        self._counter = 0
    
    def save_request(self, request: Request) -> str:
        """Сохранение запроса"""
        request_id = str(uuid.uuid4())
        request.id = request_id
        request.created_at = datetime.now()
        self._requests[request_id] = request
        self._counter += 1
        return request_id
    
    def get_request(self, request_id: str) -> Optional[Request]:
        """Получение запроса по ID"""
        return self._requests.get(request_id)
    
    def update_request_status(self, request_id: str, status: str) -> bool:
        """Обновление статуса запроса"""
        if request_id in self._requests:
            self._requests[request_id].status = status
            self._requests[request_id].updated_at = datetime.now()
            return True
        return False
    
    def get_user_requests(self, user_id: str, limit: int = 10) -> List[Request]:
        """Получение запросов пользователя"""
        user_requests = [
            req for req in self._requests.values() 
            if req.user_id == user_id
        ]
        return sorted(user_requests, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        total = len(self._requests)
        statuses = {}
        for req in self._requests.values():
            statuses[req.status] = statuses.get(req.status, 0) + 1
        
        return {
            "total_requests": total,
            "statuses": statuses,
            "counter": self._counter
        }
    
    def get_all(self) -> List[Request]:
        """Получение всех запросов"""
        return list(self._requests.values())
    
    def delete(self, entity_id: str) -> bool:
        """Удаление запроса"""
        if entity_id in self._requests:
            del self._requests[entity_id]
            return True
        return False
    
    def update(self, entity_id: str, entity: Request) -> bool:
        """Обновление запроса"""
        if entity_id in self._requests:
            entity.id = entity_id
            entity.updated_at = datetime.now()
            self._requests[entity_id] = entity
            return True
        return False
    
    def save(self, entity: Request) -> str:
        """Сохранение запроса (алиас для save_request)"""
        return self.save_request(entity)
    
    def get_by_id(self, entity_id: str) -> Optional[Request]:
        """Получение запроса по ID (алиас для get_request)"""
        return self.get_request(entity_id) 