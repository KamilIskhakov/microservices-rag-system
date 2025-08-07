"""
FAISS реализация репозитория для Vector Store Service
"""
import os
import logging
import pickle
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime

import faiss
from sentence_transformers import SentenceTransformer

from domain.repositories.vector_repository import VectorRepository
from domain.entities.vector_document import VectorDocument, SearchResult

logger = logging.getLogger(__name__)


class FAISSRepository(VectorRepository):
    """FAISS реализация репозитория векторных документов"""
    
    def __init__(self, index_path: str = "/app/data/faiss_index", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.index_path = index_path
        self.model_name = model_name
        self.documents: Dict[str, VectorDocument] = {}
        self.index = None
        self.embedding_model = None
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Загрузить или создать индекс"""
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Загружаем модель эмбеддингов
            self.embedding_model = SentenceTransformer(self.model_name)
            embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            
            # Пытаемся загрузить существующий индекс
            index_file = f"{self.index_path}.faiss"
            docs_file = f"{self.index_path}.pkl"
            
            if os.path.exists(index_file) and os.path.exists(docs_file):
                logger.info("Загружаем существующий FAISS индекс...")
                self.index = faiss.read_index(index_file)
                
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                logger.info(f"Индекс загружен: {len(self.documents)} документов")
            else:
                logger.info("Создаем новый FAISS индекс...")
                self.index = faiss.IndexFlatIP(embedding_dim)  # Inner Product для косинусного сходства
                self.documents = {}
                
        except Exception as e:
            logger.error(f"Ошибка загрузки/создания индекса: {e}")
            raise
    
    def _save_index(self):
        """Сохранить индекс"""
        try:
            index_file = f"{self.index_path}.faiss"
            docs_file = f"{self.index_path}.pkl"
            
            faiss.write_index(self.index, index_file)
            
            with open(docs_file, 'wb') as f:
                pickle.dump(self.documents, f)
                
            logger.info("Индекс сохранен")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения индекса: {e}")
    
    def save_document(self, document: VectorDocument) -> str:
        """Сохранить документ"""
        try:
            # Добавляем документ в словарь
            self.documents[document.id] = document
            
            # Добавляем эмбеддинг в индекс
            if document.embedding:
                embedding_array = np.array([document.embedding], dtype=np.float32)
                self.index.add(embedding_array)
            
            # Сохраняем индекс
            self._save_index()
            
            logger.info(f"Документ сохранен: {document.id}")
            return document.id
            
        except Exception as e:
            logger.error(f"Ошибка сохранения документа: {e}")
            raise
    
    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Получить документ по ID"""
        return self.documents.get(document_id)
    
    def search_similar(self, query_embedding: List[float], top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        """Поиск похожих документов"""
        try:
            if self.index.ntotal == 0:
                return []
            
            # Преобразуем запрос в numpy array
            query_array = np.array([query_embedding], dtype=np.float32)
            
            # Нормализуем для косинусного сходства
            faiss.normalize_L2(query_array)
            
            # Выполняем поиск
            scores, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if score >= threshold and idx != -1:
                    # Получаем документ по индексу
                    doc_id = list(self.documents.keys())[idx]
                    document = self.documents[doc_id]
                    
                    result = SearchResult(
                        document_id=document.id,
                        content=document.content,
                        relevance_score=float(score),
                        metadata=document.metadata,
                        distance=1.0 - float(score)
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return []
    
    def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """Добавить несколько документов"""
        try:
            document_ids = []
            embeddings = []
            
            for document in documents:
                self.documents[document.id] = document
                document_ids.append(document.id)
                
                if document.embedding:
                    embeddings.append(document.embedding)
            
            # Добавляем все эмбеддинги в индекс
            if embeddings:
                embeddings_array = np.array(embeddings, dtype=np.float32)
                self.index.add(embeddings_array)
            
            # Сохраняем индекс
            self._save_index()
            
            logger.info(f"Добавлено {len(documents)} документов")
            return document_ids
            
        except Exception as e:
            logger.error(f"Ошибка добавления документов: {e}")
            raise
    
    def update_document(self, document_id: str, document: VectorDocument) -> bool:
        """Обновить документ"""
        try:
            if document_id not in self.documents:
                return False
            
            # Обновляем документ
            self.documents[document_id] = document
            
            # Перестраиваем индекс
            self.rebuild_index()
            
            logger.info(f"Документ обновлен: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления документа: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Удалить документ"""
        try:
            if document_id not in self.documents:
                return False
            
            # Удаляем документ
            del self.documents[document_id]
            
            # Перестраиваем индекс
            self.rebuild_index()
            
            logger.info(f"Документ удален: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления документа: {e}")
            return False
    
    def get_all_documents(self) -> List[VectorDocument]:
        """Получить все документы"""
        return list(self.documents.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        return {
            "total_documents": len(self.documents),
            "indexed_documents": len([d for d in self.documents.values() if d.is_indexed()]),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.embedding_model.get_sentence_embedding_dimension() if self.embedding_model else 0,
            "model_name": self.model_name
        }
    
    def clear_index(self) -> bool:
        """Очистить индекс"""
        try:
            self.documents.clear()
            
            # Создаем новый индекс
            embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatIP(embedding_dim)
            
            # Сохраняем пустой индекс
            self._save_index()
            
            logger.info("Индекс очищен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка очистки индекса: {e}")
            return False
    
    def rebuild_index(self) -> bool:
        """Перестроить индекс"""
        try:
            # Создаем новый индекс
            embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatIP(embedding_dim)
            
            # Добавляем все документы с эмбеддингами
            embeddings = []
            for document in self.documents.values():
                if document.embedding:
                    embeddings.append(document.embedding)
            
            if embeddings:
                embeddings_array = np.array(embeddings, dtype=np.float32)
                self.index.add(embeddings_array)
            
            # Сохраняем индекс
            self._save_index()
            
            logger.info("Индекс перестроен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка перестроения индекса: {e}")
            return False
