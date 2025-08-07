"""
Репозиторий для работы с векторными документами в Vector Store Service
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.vector_document import VectorDocument, SearchResult


class VectorRepository(ABC):
    """Абстрактный репозиторий для работы с векторными документами"""
    
    @abstractmethod
    def save_document(self, document: VectorDocument) -> str:
        """Сохранить документ"""
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Получить документ по ID"""
        pass
    
    @abstractmethod
    def search_similar(self, query_embedding: List[float], top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        """Поиск похожих документов"""
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """Добавить несколько документов"""
        pass
    
    @abstractmethod
    def update_document(self, document_id: str, document: VectorDocument) -> bool:
        """Обновить документ"""
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Удалить документ"""
        pass
    
    @abstractmethod
    def get_all_documents(self) -> List[VectorDocument]:
        """Получить все документы"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        pass
    
    @abstractmethod
    def clear_index(self) -> bool:
        """Очистить индекс"""
        pass
    
    @abstractmethod
    def rebuild_index(self) -> bool:
        """Перестроить индекс"""
        pass
