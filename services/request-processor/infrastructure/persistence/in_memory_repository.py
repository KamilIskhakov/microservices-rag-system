"""
In-Memory реализация репозитория для Request Processor Service
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from domain.repositories.request_repository import RequestRepository
from domain.entities.request import Request

logger = logging.getLogger(__name__)


class InMemoryRequestRepository(RequestRepository):
    """In-Memory реализация репозитория запросов"""
    
    def __init__(self):
        self.requests: Dict[str, Request] = {}
        self.user_requests: Dict[str, List[str]] = defaultdict(list)
        self._request_count = 0
        self._total_processing_time = 0.0
    
    def save_request(self, request: Request) -> str:
        """Сохранить запрос"""
        request_id = str(request.id)
        self.requests[request_id] = request
        
        if request.user_id:
            self.user_requests[request.user_id].append(request_id)
        
        self._request_count += 1
        logger.info(f"Запрос сохранен: {request_id}")
        return request_id
    
    def get_request(self, request_id: str) -> Optional[Request]:
        """Получить запрос по ID"""
        return self.requests.get(request_id)
    
    def update_request_status(self, request_id: str, status: str) -> bool:
        """Обновить статус запроса"""
        if request_id in self.requests:
            self.requests[request_id].update_status(status)
            logger.info(f"Статус запроса {request_id} обновлен: {status}")
            return True
        return False
    
    def update_request_results(self, request_id: str, results: Dict[str, Any]) -> bool:
        """Обновить результаты запроса"""
        if request_id in self.requests:
            self.requests[request_id].set_results(results)
            logger.info(f"Результаты запроса {request_id} обновлены")
            return True
        return False
    
    def get_user_requests(self, user_id: str, limit: int = 10) -> List[Request]:
        """Получить запросы пользователя"""
        if user_id not in self.user_requests:
            return []
        
        request_ids = self.user_requests[user_id][-limit:]
        return [self.requests[req_id] for req_id in request_ids if req_id in self.requests]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        total_requests = len(self.requests)
        completed_requests = len([r for r in self.requests.values() if r.status == "completed"])
        failed_requests = len([r for r in self.requests.values() if r.status == "failed"])
        pending_requests = len([r for r in self.requests.values() if r.status == "pending"])
        
        avg_processing_time = 0.0
        if completed_requests > 0:
            processing_times = [r.processing_time for r in self.requests.values() if r.processing_time]
            if processing_times:
                avg_processing_time = sum(processing_times) / len(processing_times)
        
        return {
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "failed_requests": failed_requests,
            "pending_requests": pending_requests,
            "avg_processing_time": avg_processing_time,
            "unique_users": len(self.user_requests)
        }
    
    def delete_request(self, request_id: str) -> bool:
        """Удалить запрос"""
        if request_id in self.requests:
            request = self.requests[request_id]
            
            if request.user_id and request_id in self.user_requests[request.user_id]:
                self.user_requests[request.user_id].remove(request_id)
            
            del self.requests[request_id]
            
            logger.info(f"Запрос удален: {request_id}")
            return True
        return False
    
    def get_pending_requests(self) -> List[Request]:
        """Получить ожидающие запросы"""
        return [r for r in self.requests.values() if r.status == "pending"]
