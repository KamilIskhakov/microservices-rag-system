"""
Команды для работы с запросами
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from src.domain.repositories.request_repository import RequestRepository
from src.domain.entities.request import Request
from src.application.commands.command_bus import CommandBus

@dataclass
class CreateRequestCommand:
    """Команда создания запроса"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class CreateRequestResult:
    """Результат создания запроса"""
    request_id: str
    status: str = "pending"

@dataclass
class ProcessRequestCommand:
    """Команда обработки запроса"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    services: List[str] = None

@dataclass
class ProcessRequestResult:
    """Результат обработки запроса"""
    request_id: str
    results: Dict[str, Any]

class CreateRequestCommandHandler:
    """Обработчик команды создания запроса"""
    
    def __init__(self, request_repository: RequestRepository):
        self.request_repository = request_repository
    
    async def handle(self, command: CreateRequestCommand) -> CreateRequestResult:
        """Обработка команды создания запроса"""
        # Создаем запрос
        request = Request(
            id=None,  # Будет сгенерирован автоматически
            query=command.query,
            user_id=command.user_id,
            session_id=command.session_id,
            status="pending"
        )
        
        # Сохраняем запрос
        request_id = self.request_repository.save_request(request)
        
        return CreateRequestResult(
            request_id=request_id,
            status="pending"
        )

class ProcessRequestCommandHandler:
    """Обработчик команды обработки запроса"""
    
    def __init__(self, request_repository: RequestRepository):
        self.request_repository = request_repository
    
    async def handle(self, command: ProcessRequestCommand) -> ProcessRequestResult:
        """Обработка команды обработки запроса"""
        # Создаем запрос
        request = Request(
            id=None,
            query=command.query,
            user_id=command.user_id,
            session_id=command.session_id,
            status="processing"
        )
        
        # Сохраняем запрос
        request_id = self.request_repository.save_request(request)
        
        # Здесь должна быть логика координации сервисов
        # Пока возвращаем заглушку
        results = {
            "ai-model": {"status": "processed"},
            "vectorstore": {"status": "processed"}
        }
        
        # Обновляем статус запроса
        self.request_repository.update_request_status(request_id, "completed")
        
        return ProcessRequestResult(
            request_id=request_id,
            results=results
        ) 