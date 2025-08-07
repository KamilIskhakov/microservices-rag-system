"""
Доменный сервис для работы с векторными документами в Vector Store Service
"""
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer

from ..entities.vector_document import VectorDocument, SearchResult
from ..repositories.vector_repository import VectorRepository


class VectorService:
    """Доменный сервис для работы с векторными документами"""
    
    def __init__(self, vector_repository: VectorRepository, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.vector_repository = vector_repository
        self.model_name = model_name
        self._embedding_model = None
    
    def _get_embedding_model(self) -> SentenceTransformer:
        """Получить модель для эмбеддингов"""
        if self._embedding_model is None:
            self._embedding_model = SentenceTransformer(self.model_name)
        return self._embedding_model
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Добавить документ"""
        # Создаем документ
        document = VectorDocument(
            id=None,
            content=content,
            metadata=metadata
        )
        
        # Генерируем эмбеддинг
        embedding = self._get_embedding_model().encode(content)
        document.update_embedding(embedding.tolist())
        
        # Сохраняем документ
        return self.vector_repository.save_document(document)
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Добавить несколько документов"""
        vector_documents = []
        
        for doc_data in documents:
            document = VectorDocument(
                id=None,
                content=doc_data["content"],
                metadata=doc_data.get("metadata", {})
            )
            vector_documents.append(document)
        
        # Генерируем эмбеддинги для всех документов
        contents = [doc.content for doc in vector_documents]
        embeddings = self._get_embedding_model().encode(contents)
        
        # Обновляем документы с эмбеддингами
        for i, document in enumerate(vector_documents):
            document.update_embedding(embeddings[i].tolist())
        
        # Сохраняем документы
        return self.vector_repository.add_documents(vector_documents)
    
    async def search_similar(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        """Поиск похожих документов"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"VectorService: generating embedding for query: {query[:50]}...")
            
            # Генерируем эмбеддинг для запроса
            query_embedding = self._get_embedding_model().encode(query)
            logger.info(f"VectorService: embedding generated, length: {len(query_embedding)}")
            
            # Ищем похожие документы
            logger.info(f"VectorService: calling repository.search_similar with top_k={top_k}, threshold={threshold}")
            
            results = await self.vector_repository.search_similar(
                query_embedding=query_embedding.tolist(),
                top_k=top_k,
                threshold=threshold
            )
            
            logger.info(f"VectorService: search completed, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"VectorService: error in search_similar: {e}")
            raise
    
    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Получить документ по ID"""
        return self.vector_repository.get_document(document_id)
    
    def update_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Обновить документ"""
        # Получаем существующий документ
        existing_doc = self.vector_repository.get_document(document_id)
        if not existing_doc:
            return False
        
        # Обновляем содержимое и метаданные
        existing_doc.content = content
        existing_doc.update_metadata(metadata)
        
        # Генерируем новый эмбеддинг
        embedding = self._get_embedding_model().encode(content)
        existing_doc.update_embedding(embedding.tolist())
        
        # Сохраняем обновленный документ
        return self.vector_repository.update_document(document_id, existing_doc)
    
    def delete_document(self, document_id: str) -> bool:
        """Удалить документ"""
        return self.vector_repository.delete_document(document_id)
    
    def get_all_documents(self) -> List[VectorDocument]:
        """Получить все документы"""
        return self.vector_repository.get_all_documents()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        return await self.vector_repository.get_statistics()
    
    def clear_index(self) -> bool:
        """Очистить индекс"""
        return self.vector_repository.clear_index()
    
    def rebuild_index(self) -> bool:
        """Перестроить индекс"""
        return self.vector_repository.rebuild_index()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Получить информацию о модели"""
        model = self._get_embedding_model()
        return {
            "model_name": self.model_name,
            "max_seq_length": model.max_seq_length,
            "embedding_dimension": model.get_sentence_embedding_dimension()
        }
