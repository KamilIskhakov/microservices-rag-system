"""
FAISS реализация репозитория векторного хранилища
"""
import logging
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

import faiss
from sentence_transformers import SentenceTransformer

from src.domain.repositories.vector_repository import VectorRepository
from src.domain.entities.vector_document import VectorDocument
from src.domain.strategies.search_strategy import SearchResult

logger = logging.getLogger(__name__)

class FaissVectorRepository(VectorRepository):
    """FAISS реализация репозитория векторного хранилища"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.encoder = None
        self.index = None
        self.documents: Dict[str, VectorDocument] = {}
        self.document_ids: List[str] = []  # Сохраняем порядок документов
        self.index_path = "/app/data/faiss_index"
        self.documents_path = "/app/data/documents.json"
        self._load_encoder()
        self._load_from_disk()
    
    def _load_encoder(self):
        """Загружает энкодер для создания эмбеддингов"""
        try:
            logger.info(f"Loading encoder: {self.model_name}")
            self.encoder = SentenceTransformer(self.model_name)
            logger.info("Encoder loaded successfully")
        except Exception as e:
            logger.error(f"Error loading encoder: {e}")
            # Используем заглушку если энкодер не загрузился
            self.encoder = None
    
    def add_document(self, document: VectorDocument) -> str:
        """Добавление документа"""
        doc_id = str(uuid.uuid4())
        document.id = doc_id
        document.created_at = datetime.now()
        self.documents[doc_id] = document
        self.document_ids.append(doc_id)
        
        # Если есть энкодер, добавляем в FAISS индекс
        if self.encoder and document.text:
            self._add_to_faiss_index(doc_id, document.text)
        
        return doc_id
    
    def add_documents_batch(self, documents: List[VectorDocument]) -> List[str]:
        """Быстрое добавление множества документов"""
        if not documents:
            return []
        
        doc_ids = []
        texts = []
        
        # Подготавливаем документы
        for document in documents:
            doc_id = str(uuid.uuid4())
            document.id = doc_id
            document.created_at = datetime.now()
            self.documents[doc_id] = document
            self.document_ids.append(doc_id)
            doc_ids.append(doc_id)
            
            if document.text:
                texts.append(document.text)
        
        # Если есть энкодер и тексты, добавляем batch в FAISS
        if self.encoder and texts:
            self._add_batch_to_faiss_index(doc_ids, texts)
        
        logger.info(f"Добавлено {len(documents)} документов в Vector Store")
        
        # Сохраняем на диск после batch добавления
        self._save_to_disk()
        
        return doc_ids
    
    def _add_to_faiss_index(self, doc_id: str, text: str):
        """Добавляет документ в FAISS индекс"""
        try:
            # Создаем эмбеддинг
            embedding = self.encoder.encode([text])
            
            # Инициализируем индекс если он еще не создан
            if self.index is None:
                dimension = embedding.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # Inner Product для косинусного сходства
            
            # Нормализуем эмбеддинг для косинусного сходства
            faiss.normalize_L2(embedding)
            
            # Добавляем в индекс
            self.index.add(embedding.astype('float32'))
            
            logger.debug(f"Added document {doc_id} to FAISS index")
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id} to FAISS index: {e}")
    
    def _add_batch_to_faiss_index(self, doc_ids: List[str], texts: List[str]):
        """Быстрое добавление множества документов в FAISS индекс"""
        try:
            # Создаем эмбеддинги для всех текстов сразу
            embeddings = self.encoder.encode(texts)
            
            # Инициализируем индекс если он еще не создан
            if self.index is None:
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # Inner Product для косинусного сходства
            
            # Нормализуем эмбеддинги для косинусного сходства
            faiss.normalize_L2(embeddings)
            
            # Добавляем batch в индекс
            self.index.add(embeddings.astype('float32'))
            
            logger.info(f"Добавлено {len(texts)} документов в FAISS индекс за один раз")
            
        except Exception as e:
            logger.error(f"Error adding batch to FAISS index: {e}")
    
    def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Получение документа по ID"""
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Удаление документа"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            if doc_id in self.document_ids:
                self.document_ids.remove(doc_id)
            return True
        return False
    
    def clear_all(self) -> bool:
        """Очистка всех документов"""
        try:
            self.documents.clear()
            self.document_ids.clear()
            self.index = None  # Сбрасываем FAISS индекс
            logger.info("Все документы очищены из Vector Store")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки документов: {e}")
            return False
    
    def remove_documents_by_filter(self, filter_func) -> int:
        """Удаление документов по фильтру"""
        try:
            documents_to_remove = []
            for doc_id, document in self.documents.items():
                if filter_func(document):
                    documents_to_remove.append(doc_id)
            
            # Удаляем документы
            for doc_id in documents_to_remove:
                del self.documents[doc_id]
                if doc_id in self.document_ids:
                    self.document_ids.remove(doc_id)
            
            # Пересоздаем FAISS индекс без удаленных документов
            if documents_to_remove:
                self._rebuild_faiss_index()
                self._save_to_disk()
                logger.info(f"Удалено {len(documents_to_remove)} документов из Vector Store")
            
            return len(documents_to_remove)
        except Exception as e:
            logger.error(f"Ошибка удаления документов: {e}")
            return 0
    
    def _rebuild_faiss_index(self):
        """Пересоздание FAISS индекса"""
        try:
            if not self.documents:
                self.index = None
                return
            
            # Собираем все тексты
            texts = []
            doc_ids = []
            for doc_id in self.document_ids:
                if doc_id in self.documents:
                    doc = self.documents[doc_id]
                    if doc.text:
                        texts.append(doc.text)
                        doc_ids.append(doc_id)
            
            if not texts:
                self.index = None
                return
            
            # Создаем эмбеддинги
            embeddings = self.encoder.encode(texts)
            
            # Создаем новый индекс
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            
            # Нормализуем и добавляем
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype('float32'))
            
            # Обновляем document_ids
            self.document_ids = doc_ids
            
            logger.info(f"FAISS индекс пересоздан с {len(texts)} документами")
        except Exception as e:
            logger.error(f"Ошибка пересоздания FAISS индекса: {e}")
    
    def search_documents(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        """Поиск документов с гибридной стратегией"""
        from src.infrastructure.strategies.exact_search_strategy import ExactSearchStrategy
        from src.infrastructure.strategies.semantic_search_strategy import SemanticSearchStrategy
        from src.infrastructure.strategies.hybrid_search_strategy import HybridSearchStrategy
        
        # Создаем стратегии
        exact_strategy = ExactSearchStrategy()
        semantic_strategy = SemanticSearchStrategy(self.encoder, self.index, self.document_ids)
        hybrid_strategy = HybridSearchStrategy(exact_strategy, semantic_strategy)
        
        # Получаем все документы
        documents = list(self.documents.values())
        
        # Выполняем гибридный поиск
        results = hybrid_strategy.search(query, documents, top_k)
        
        # Преобразуем в формат SearchResult для совместимости с Vector Store Service
        search_results = []
        for result in results:
            # Создаем SearchResult в формате, ожидаемом Vector Store Service
            from src.domain.entities.vector_document import SearchResult as VectorSearchResult
            search_results.append(VectorSearchResult(
                document=result.document,
                relevance_score=result.score
            ))
        
        return search_results
    
    def _faiss_search(self, query: str, top_k: int) -> List[SearchResult]:
        """FAISS поиск"""
        if not self.documents or self.index is None:
            return []
        
        try:
            # Создаем эмбеддинг для запроса
            query_embedding = self.encoder.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Выполняем поиск
            scores, indices = self.index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(self.documents))
            )
            
            # Формируем результаты
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.document_ids):
                    doc_id = self.document_ids[idx]
                    doc = self.documents[doc_id]
                    
                    # В FAISS большее значение = лучшая релевантность
                    # Но мы хотим меньшие значения для лучшей релевантности
                    relevance_score = 1.0 - float(score)
                    
                    results.append(SearchResult(
                        document=doc,
                        relevance_score=relevance_score,
                        rank=len(results)
                    ))
            
            logger.info(f"FAISS search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in FAISS search: {e}")
            return []
    
    def _save_to_disk(self):
        """Сохраняет FAISS индекс и документы на диск"""
        try:
            import os
            import json
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Сохраняем FAISS индекс
            if self.index is not None:
                faiss.write_index(self.index, self.index_path)
                logger.info(f"FAISS индекс сохранен: {self.index_path}")
            
            # Сохраняем документы
            documents_data = {}
            for doc_id, doc in self.documents.items():
                documents_data[doc_id] = {
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
            
            with open(self.documents_path, 'w', encoding='utf-8') as f:
                json.dump(documents_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Документы сохранены: {self.documents_path}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения на диск: {e}")
    
    def _load_from_disk(self):
        """Загружает FAISS индекс и документы с диска"""
        try:
            import os
            import json
            from datetime import datetime
            
            # Загружаем FAISS индекс
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                logger.info(f"FAISS индекс загружен: {self.index_path}")
            
            # Загружаем документы
            if os.path.exists(self.documents_path):
                with open(self.documents_path, 'r', encoding='utf-8') as f:
                    documents_data = json.load(f)
                
                for doc_id, doc_data in documents_data.items():
                    doc = VectorDocument(
                        id=doc_data["id"],
                        text=doc_data["text"],
                        metadata=doc_data.get("metadata", {}),
                        created_at=datetime.fromisoformat(doc_data["created_at"]) if doc_data.get("created_at") else None
                    )
                    self.documents[doc_id] = doc
                    self.document_ids.append(doc_id)
                
                logger.info(f"Загружено {len(self.documents)} документов с диска")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки с диска: {e}")
    
    def reindex(self) -> bool:
        """Переиндексация"""
        try:
            if self.encoder is None:
                return True
            
            # Очищаем индекс
            self.index = None
            
            # Пересоздаем индекс
            for doc_id in self.document_ids:
                doc = self.documents[doc_id]
                if doc.text:
                    self._add_to_faiss_index(doc_id, doc.text)
            
            logger.info("Vector store reindexed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error reindexing: {e}")
            return False
    
    def get_documents_count(self) -> int:
        """Получение количества документов"""
        return len(self.documents)
    
    def get_size(self) -> int:
        """Получение размера хранилища"""
        return len(self.documents)
    
    def get_info(self) -> Dict[str, Any]:
        """Получение информации о хранилище"""
        return {
            "documents_count": len(self.documents),
            "faiss_index_size": self.index.ntotal if self.index else 0,
            "encoder_loaded": self.encoder is not None,
            "model_name": self.model_name
        } 

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        return {
            "documents_count": len(self.documents),
            "faiss_index_size": self.index.ntotal if self.index else 0,
            "encoder_loaded": self.encoder is not None,
            "model_name": self.model_name,
            "last_updated": datetime.now().isoformat()
        } 

    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Поиск документов (совместимость с Vector Store Service)"""
        results = self.search_documents(query, top_k)
        
        # Преобразуем в формат, ожидаемый Vector Store Service
        formatted_results = []
        for result in results:
            formatted_results.append({
                "text": result.document.text,
                "relevance_score": result.relevance_score,
                "metadata": result.document.metadata or {}
            })
        
        return formatted_results 