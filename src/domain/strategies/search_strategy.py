from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.domain.entities.vector_document import VectorDocument


class SearchResult:
    """Результат поиска"""
    def __init__(self, document: VectorDocument, score: float, search_type: str):
        self.document = document
        self.score = score
        self.search_type = search_type


class SearchStrategy(ABC):
    """Абстрактная стратегия поиска"""
    
    @abstractmethod
    def search(self, query: str, documents: List[VectorDocument], top_k: int = 5) -> List[SearchResult]:
        """Поиск документов"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Название стратегии"""
        pass


class SearchStrategyFactory:
    """Фабрика стратегий поиска"""
    
    def __init__(self):
        self._strategies: Dict[str, SearchStrategy] = {}
    
    def register_strategy(self, strategy: SearchStrategy):
        """Регистрация стратегии"""
        self._strategies[strategy.get_strategy_name()] = strategy
    
    def get_strategy(self, name: str) -> SearchStrategy:
        """Получение стратегии по имени"""
        if name not in self._strategies:
            raise ValueError(f"Стратегия '{name}' не найдена")
        return self._strategies[name]
    
    def get_all_strategies(self) -> List[SearchStrategy]:
        """Получение всех стратегий"""
        return list(self._strategies.values()) 