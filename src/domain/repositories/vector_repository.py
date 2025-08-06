"""
Репозиторий для векторного хранилища
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.entities.vector_document import VectorDocument, SearchResult

class VectorRepository(ABC):
    """Абстрактный репозиторий для векторного хранилища"""
    
    @abstractmethod
    def add_document(self, document: VectorDocument) -> str:
        """Добавление документа"""
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Получение документа по ID"""
        pass
    
    @abstractmethod
    def search_documents(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        """Поиск документов"""
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Удаление документа"""
        pass
    
    @abstractmethod
    def get_documents_count(self) -> int:
        """Получение количества документов"""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Получение информации о хранилище"""
        pass
    
    @abstractmethod
    def reindex(self) -> Dict[str, Any]:
        """Переиндексация документов"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        pass

class InMemoryVectorRepository(VectorRepository):
    """In-memory реализация репозитория векторного хранилища"""
    
    def __init__(self):
        self.documents: Dict[str, VectorDocument] = {}
        self.index_ready = False
    
    def add_document(self, document: VectorDocument) -> str:
        """Добавление документа"""
        self.documents[document.id] = document
        return document.id
    
    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Получение документа по ID"""
        return self.documents.get(document_id)
    
    def search_documents(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        """Поиск документов (заглушка)"""
        # Здесь должна быть реальная логика поиска
        # Пока возвращаем заглушку
        results = []
        for i, document in enumerate(list(self.documents.values())[:top_k]):
            # Симуляция релевантности
            relevance_score = 0.5 + (i * 0.1)  # Уменьшаем релевантность с каждым документом
            if relevance_score <= threshold:
                results.append(SearchResult(
                    document=document,
                    relevance_score=relevance_score,
                    rank=i
                ))
        return results
    
    def delete_document(self, document_id: str) -> bool:
        """Удаление документа"""
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False
    
    def get_documents_count(self) -> int:
        """Получение количества документов"""
        return len(self.documents)
    
    def get_info(self) -> Dict[str, Any]:
        """Получение информации о хранилище"""
        return {
            "documents_count": len(self.documents),
            "index_ready": self.index_ready,
            "storage_type": "in_memory",
            "last_updated": datetime.now().isoformat()
        }
    
    def reindex(self) -> Dict[str, Any]:
        """Переиндексация документов"""
        # Симуляция переиндексации
        self.index_ready = True
        return {
            "documents_processed": len(self.documents),
            "index_ready": True,
            "processing_time": 1.0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        return {
            "total_documents": len(self.documents),
            "index_ready": self.index_ready,
            "average_document_length": sum(
                len(doc.text) for doc in self.documents.values()
            ) / len(self.documents) if self.documents else 0
        } 