"""
Command Bus для обработки команд
"""
from typing import Dict, Type, Any, Callable
from abc import ABC, abstractmethod

class CommandHandler(ABC):
    """Базовый класс для обработчиков команд"""
    
    @abstractmethod
    async def handle(self, command: Any) -> Any:
        """Обработка команды"""
        pass

class CommandBus:
    """Шина команд для диспетчеризации команд к обработчикам"""
    
    def __init__(self):
        self._handlers: Dict[Type, CommandHandler] = {}
    
    def register_handler(self, command_type: Type, handler: CommandHandler):
        """Регистрация обработчика для типа команды"""
        self._handlers[command_type] = handler
    
    async def handle(self, command: Any) -> Any:
        """Обработка команды"""
        command_type = type(command)
        
        if command_type not in self._handlers:
            raise ValueError(f"Обработчик для команды {command_type} не найден")
        
        handler = self._handlers[command_type]
        return await handler.handle(command) 