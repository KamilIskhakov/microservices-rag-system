from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedMaterial:
    """Модель данных для экстремистского материала"""
    title: str
    description: str
    decision_date: datetime
    decision_number: str
    source_url: str
    category: str = "экстремистские материалы"
    is_active: bool = True


class BaseParser(ABC):
    """Базовый интерфейс для всех парсеров"""
    
    @abstractmethod
    async def parse_materials(self) -> List[ParsedMaterial]:
        """Парсит материалы с источника"""
        pass
    
    @abstractmethod
    async def get_last_update_date(self) -> datetime:
        """Получает дату последнего обновления источника"""
        pass
    
    @abstractmethod
    async def validate_source(self) -> bool:
        """Проверяет доступность источника"""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Возвращает название источника"""
        pass


class ParserResult:
    """Результат парсинга"""
    
    def __init__(self, success: bool, materials: List[ParsedMaterial] = None, error: str = None):
        self.success = success
        self.materials = materials or []
        self.error = error
        self.timestamp = datetime.now()
    
    def __bool__(self):
        return self.success
    
    def get_materials_count(self) -> int:
        return len(self.materials)
    
    def has_error(self) -> bool:
        return self.error is not None 