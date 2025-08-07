import faiss
import numpy as np
import asyncio
import pickle
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import redis.asyncio as redis
from sentence_transformers import SentenceTransformer
import torch
from domain.entities.vector_document import SearchResult

from domain.repositories.vector_repository import VectorRepository
from domain.entities.vector_document import VectorDocument, SearchResult

logger = logging.getLogger(__name__)

class OptimizedFAISSRepository(VectorRepository):
    """
    Продакшн-оптимизированная реализация FAISS репозитория
    с кэшированием, батчингом и оптимизацией памяти
    """
    
    def __init__(self, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 index_type: str = "IndexIVFFlat",
                 nlist: int = 100,
                 nprobe: int = 10,
                 cache_ttl: int = 3600):
        
        # Инициализация модели эмбеддингов
        self.model = SentenceTransformer(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        # FAISS индекс
        self.index = None
        self.index_type = index_type
        self.nlist = nlist
        self.nprobe = nprobe
        
        # Кэширование
        self.redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
        self.cache_ttl = cache_ttl
        
        # Локальный кэш документов
        self.documents_cache = {}
        self.embeddings_cache = {}
        
        # ThreadPool для CPU операций
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Метрики
        self.search_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Загрузка существующего индекса
        self._load_index()
    
    def _load_index(self):
        """Загрузка существующего индекса"""
        try:
            if os.path.exists("/app/data/faiss_index"):
                self.index = faiss.read_index("/app/data/faiss_index")
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
                
                # Загружаем документы из JSON файла
                if os.path.exists("/app/data/documents.json"):
                    with open("/app/data/documents.json", "r", encoding="utf-8") as f:
                        documents_data = json.load(f)
                        # Сортируем документы по ID для соответствия индексам FAISS
                        sorted_docs = sorted(documents_data.items(), key=lambda x: x[0])
                        
                        for i, (doc_id, doc_data) in enumerate(sorted_docs):
                            # Поддерживаем как старый формат (text), так и новый (content)
                            content = doc_data.get("content") or doc_data.get("text", "")
                            document = VectorDocument(
                                id=str(i),  # Используем числовой индекс как ID
                                content=content,
                                metadata=doc_data.get("metadata", {})
                            )
                            self.documents_cache[str(i)] = document
                    logger.info(f"Loaded {len(self.documents_cache)} documents from cache with numeric IDs")
            else:
                self._create_new_index()
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Создание нового оптимизированного индекса"""
        dimension = self.model.get_sentence_embedding_dimension()
        
        if self.index_type == "IndexIVFFlat":
            # Квантизированный индекс для быстрого поиска
            quantizer = faiss.IndexFlatIP(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, self.nlist)
            self.index.nprobe = self.nprobe
        elif self.index_type == "IndexHNSW":
            # Иерархический индекс для высокой точности
            self.index = faiss.IndexHNSWFlat(dimension, 32)  # 32 соседа
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 100
        else:
            # Простой индекс для точного поиска
            self.index = faiss.IndexFlatIP(dimension)
        
        logger.info(f"Created new {self.index_type} index with dimension {dimension}")
    
    async def save_document(self, document: VectorDocument) -> str:
        """Сохранение документа с оптимизацией"""
        try:
            # Генерация эмбеддинга
            embedding = await self._generate_embedding(document.content)
            
            # Добавление в индекс
            embedding_array = np.array([embedding], dtype=np.float32)
            
            if self.index_type == "IndexIVFFlat" and not self.index.is_trained:
                # Тренировка индекса при необходимости
                self.index.train(embedding_array)
            
            self.index.add(embedding_array)
            
            # Сохранение документа в кэш
            doc_id = str(len(self.documents_cache))
            self.documents_cache[doc_id] = document
            document.id = doc_id
            
            # Кэширование эмбеддинга
            cache_key = f"embedding:{doc_id}"
            await self.redis_client.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps(embedding.tolist())
            )
            
            # Сохранение индекса на диск
            await self._save_index_async()
            
            logger.info(f"Saved document {doc_id} with embedding size {len(embedding)}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            raise
    
    async def search_similar(self, query_embedding: List[float], 
                           top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        """Оптимизированный поиск с кэшированием"""
        
        logger.info(f"OptimizedFAISSRepository: starting search with top_k={top_k}, threshold={threshold}")
        
        # Создаем ключ кэша
        query_hash = hash(tuple(query_embedding))
        cache_key = f"search:{query_hash}:{top_k}:{threshold}"
        
        # Проверяем кэш
        cached_result = await self.redis_client.get(cache_key)
        if cached_result:
            self.cache_hits += 1
            logger.info("OptimizedFAISSRepository: returning cached result")
            cached_data = json.loads(cached_result)
            # Преобразуем словари обратно в объекты SearchResult
            results = []
            for item in cached_data:
                result = SearchResult(
                    document_id=item["document_id"],
                    content=item["content"],
                    relevance_score=item["relevance_score"],
                    metadata=item["metadata"],
                    distance=item.get("distance")
                )
                results.append(result)
            return results
        
        self.cache_misses += 1
        self.search_count += 1
        
        try:
            logger.info(f"Starting search with query embedding length: {len(query_embedding)}")
            
            # Нормализация вектора запроса
            query_vector = np.array(query_embedding, dtype=np.float32)
            query_vector = query_vector / np.linalg.norm(query_vector)
            
            # Поиск в FAISS
            search_k = min(top_k * 2, self.index.ntotal)
            logger.info(f"Searching FAISS index with k={search_k}, total vectors={self.index.ntotal}")
            
            similarities, indices = self.index.search(
                query_vector.reshape(1, -1), 
                search_k
            )
            
            # Фильтрация и формирование результатов
            results = []
            logger.info(f"Search: found {len(similarities[0])} candidates, threshold={threshold}, cache_size={len(self.documents_cache)}")
            
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity >= threshold and len(results) < top_k:
                    # Получаем документ из кэша
                    doc_id = str(idx)
                    document = self.documents_cache.get(doc_id)
                    
                    if document:
                        result = SearchResult(
                            document_id=doc_id,
                            content=document.content,
                            metadata=document.metadata,
                            relevance_score=float(similarity)
                        )
                        results.append(result)
                    else:
                        logger.warning(f"Document {doc_id} not found in cache")
            
            # Кэшируем результат
            await self.redis_client.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps([result.__dict__ for result in results])
            )
            
            logger.info(f"Search completed: {len(results)} results, similarity range: {min(similarities[0]):.3f}-{max(similarities[0]):.3f}")
            return results
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Генерация эмбеддинга с кэшированием"""
        
        # Проверяем кэш
        text_hash = hash(text)
        cache_key = f"embedding_gen:{text_hash}"
        
        cached_embedding = await self.redis_client.get(cache_key)
        if cached_embedding:
            return json.loads(cached_embedding)
        
        # Генерируем эмбеддинг в отдельном потоке
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            self.executor,
            self._generate_embedding_sync,
            text
        )
        
        # Кэшируем результат
        await self.redis_client.setex(
            cache_key, 
            self.cache_ttl, 
            json.dumps(embedding.tolist())
        )
        
        return embedding.tolist()
    
    def _generate_embedding_sync(self, text: str) -> np.ndarray:
        """Синхронная генерация эмбеддинга"""
        with torch.no_grad():
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
    
    async def _save_index_async(self):
        """Асинхронное сохранение индекса"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                faiss.write_index,
                self.index,
                "/app/data/faiss_index"
            )
            
            # Сохраняем документы в JSON файл
            documents_data = {}
            for doc_id, document in self.documents_cache.items():
                documents_data[doc_id] = {
                    "id": doc_id,
                    "text": document.content,  # Используем "text" для совместимости
                    "metadata": document.metadata,
                    "created_at": datetime.now().isoformat()
                }
            
            await loop.run_in_executor(
                self.executor,
                lambda: json.dump(documents_data, open("/app/data/documents.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            )
            
            logger.info("Index and documents saved successfully")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики производительности"""
        return {
            "total_documents": len(self.documents_cache),
            "index_size": self.index.ntotal if self.index else 0,
            "search_count": self.search_count,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "index_type": self.index_type,
            "device": str(self.device),
            "memory_usage_mb": self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> float:
        """Получение использования памяти"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0.0
    
    async def rebuild_index(self):
        """Перестроение индекса с оптимизацией"""
        logger.info("Starting index rebuild...")
        
        # Создаем новый индекс
        self._create_new_index()
        
        # Перестраиваем из кэша
        for doc_id, document in self.documents_cache.items():
            embedding = await self._generate_embedding(document.content)
            embedding_array = np.array([embedding], dtype=np.float32)
            
            if self.index_type == "IndexIVFFlat" and not self.index.is_trained:
                self.index.train(embedding_array)
            
            self.index.add(embedding_array)
        
        # Сохраняем новый индекс
        await self._save_index_async()
        
        logger.info(f"Index rebuild completed: {self.index.ntotal} vectors")
    
    async def optimize_memory(self):
        """Оптимизация памяти"""
        # Очистка кэша Redis
        await self.redis_client.flushdb()
        
        # Очистка локального кэша
        self.embeddings_cache.clear()
        
        # Принудительная сборка мусора
        import gc
        gc.collect()
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Memory optimization completed")

    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Получить документ по ID"""
        return self.documents_cache.get(document_id)
    
    def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """Добавить несколько документов"""
        document_ids = []
        for document in documents:
            try:
                doc_id = asyncio.run(self.save_document(document))
                document_ids.append(doc_id)
            except Exception as e:
                logger.error(f"Error adding document: {e}")
        return document_ids
    
    def update_document(self, document_id: str, document: VectorDocument) -> bool:
        """Обновить документ"""
        try:
            if document_id in self.documents_cache:
                # Удаляем старый документ из индекса
                # (FAISS не поддерживает обновление, поэтому пересоздаем)
                self.delete_document(document_id)
                # Добавляем обновленный документ
                asyncio.run(self.save_document(document))
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Удалить документ"""
        try:
            if document_id in self.documents_cache:
                del self.documents_cache[document_id]
                # FAISS не поддерживает удаление отдельных векторов
                # Поэтому пересоздаем индекс без удаленного документа
                self._rebuild_index_without_document(document_id)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def get_all_documents(self) -> List[VectorDocument]:
        """Получить все документы"""
        return list(self.documents_cache.values())
    
    def clear_index(self) -> bool:
        """Очистить индекс"""
        try:
            self.documents_cache.clear()
            self.embeddings_cache.clear()
            self._create_new_index()
            return True
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return False
    
    def _rebuild_index_without_document(self, document_id: str):
        """Пересоздать индекс без указанного документа"""
        try:
            # Создаем новый индекс
            self._create_new_index()
            
            # Добавляем все документы кроме удаленного
            for doc_id, document in self.documents_cache.items():
                if doc_id != document_id:
                    embedding = asyncio.run(self._generate_embedding(document.content))
                    embedding_array = np.array([embedding], dtype=np.float32)
                    self.index.add(embedding_array)
        except Exception as e:
            logger.error(f"Error rebuilding index without document: {e}")
    
    async def _rebuild_index_async(self):
        """Асинхронное пересоздание индекса"""
        try:
            # Сохраняем текущие документы
            documents = list(self.documents_cache.values())
            
            # Очищаем кэши
            self.documents_cache.clear()
            self.embeddings_cache.clear()
            
            # Создаем новый индекс
            self._create_new_index()
            
            # Пересоздаем документы
            for document in documents:
                await self.save_document(document)
                
            logger.info("Index rebuilt successfully")
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
            raise
