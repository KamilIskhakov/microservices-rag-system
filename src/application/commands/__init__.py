"""
Команды приложения
"""
from typing import Type, TypeVar, Dict, Any, Callable
from abc import ABC, abstractmethod

T = TypeVar('T')

class CommandBus:
    """Шина команд для обработки команд"""
    
    def __init__(self):
        self.handlers: Dict[Type, Callable] = {}
    
    def register_handler(self, command_type: Type[T], handler: Callable[[T], Any]):
        """Регистрация обработчика команды"""
        self.handlers[command_type] = handler
    
    async def handle(self, command: T) -> Any:
        """Обработка команды"""
        command_type = type(command)
        
        if command_type not in self.handlers:
            raise ValueError(f"No handler registered for command type {command_type}")
        
        handler = self.handlers[command_type]
        return await handler(command) 