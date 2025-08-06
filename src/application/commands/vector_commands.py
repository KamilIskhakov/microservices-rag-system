"""
Команды для работы с векторным хранилищем
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from src.domain.repositories.vector_repository import VectorRepository
from src.domain.entities.vector_document import VectorDocument, SearchResult
from src.application.commands.command_bus import CommandBus

@dataclass
class AddDocumentCommand:
    """Команда добавления документа"""
    text: str
    metadata: Dict[str, Any] = None
    embedding: Optional[List[float]] = None

@dataclass
class AddDocumentResult:
    """Результат добавления документа"""
    document_id: str
    success: bool = True

@dataclass
class SearchDocumentsCommand:
    """Команда поиска документов"""
    query: str
    top_k: int = 5
    threshold: float = 0.3

@dataclass
class SearchDocumentsResult:
    """Результат поиска документов"""
    documents: List[SearchResult]
    total_found: int

class AddDocumentCommandHandler:
    """Обработчик команды добавления документа"""
    
    def __init__(self, vector_repository: VectorRepository):
        self.vector_repository = vector_repository
    
    async def handle(self, command: AddDocumentCommand) -> AddDocumentResult:
        """Обработка команды добавления документа"""
        # Создаем документ
        document = VectorDocument(
            id=None,  # Будет сгенерирован автоматически
            text=command.text,
            embedding=command.embedding,
            metadata=command.metadata or {}
        )
        
        # Добавляем документ
        document_id = self.vector_repository.add_document(document)
        
        return AddDocumentResult(
            document_id=document_id,
            success=True
        )

class SearchDocumentsCommandHandler:
    """Обработчик команды поиска документов"""
    
    def __init__(self, vector_repository: VectorRepository):
        self.vector_repository = vector_repository
    
    async def handle(self, command: SearchDocumentsCommand) -> SearchDocumentsResult:
        """Обработка команды поиска документов"""
        # Выполняем поиск
        documents = self.vector_repository.search_documents(
            query=command.query,
            top_k=command.top_k,
            threshold=command.threshold
        )
        
        return SearchDocumentsResult(
            documents=documents,
            total_found=len(documents)
        ) 