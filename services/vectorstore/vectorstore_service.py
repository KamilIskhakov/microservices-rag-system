"""
Vector Store Service - работа с векторной базой данных
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

import redis
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.domain.entities.vector_document import VectorDocument
from src.infrastructure.persistence.faiss_repository import FaissVectorRepository
from src.application.commands.vector_commands import (
    AddDocumentCommand,
    AddDocumentCommandHandler,
    SearchDocumentsCommand,
    SearchDocumentsCommandHandler,
    CommandBus
)
from src.shared.utils.logger import logger

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logger

app = FastAPI(title="RAG Vector Store Service", version="2.0.0")

# Подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Глобальные переменные
vector_repository: Optional[FaissVectorRepository] = None
command_bus: Optional[CommandBus] = None

class DocumentRequest(BaseModel):
    """Запрос на добавление документа"""
    text: str
    metadata: Dict[str, Any] = {}
    embedding: Optional[List[float]] = None

class SearchRequest(BaseModel):
    """Запрос на поиск документов"""
    query: str
    top_k: int = 5
    threshold: float = 0.3

class SearchResult(BaseModel):
    """Результат поиска"""
    text: str
    relevance_score: float
    metadata: Dict[str, Any] = {}

class SearchResponse(BaseModel):
    """Ответ на поиск"""
    success: bool
    results: List[SearchResult] = []
    total_found: int = 0
    processing_time: float = 0.0
    timestamp: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Ответ проверки здоровья"""
    status: str
    service: str
    timestamp: str
    dependencies: Dict[str, str]
    vector_store_info: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global vector_repository, command_bus
    
    try:
        logger.info("🚀 Инициализация Vector Store Service с FAISS...")
        
        # Инициализируем FAISS репозиторий
        vector_repository = FaissVectorRepository()
        
        # Инициализируем шину команд
        command_bus = CommandBus()
        
        # Регистрируем обработчики команд
        command_bus.register_handler(
            AddDocumentCommand,
            AddDocumentCommandHandler(vector_repository)
        )
        
        command_bus.register_handler(
            SearchDocumentsCommand,
            SearchDocumentsCommandHandler(vector_repository)
        )
        
        logger.info("✅ Vector Store Service с FAISS готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Vector Store Service: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверяем Redis
        redis_healthy = "healthy"
        try:
            redis_client.ping()
        except:
            redis_healthy = "unhealthy"
        
        # Получаем информацию о векторном хранилище
        vector_info = vector_repository.get_info() if vector_repository else {}
        
        dependencies = {
            "redis": redis_healthy,
            "faiss": "healthy" if vector_repository else "unhealthy"
        }
        
        return HealthResponse(
            status="healthy" if redis_healthy == "healthy" else "unhealthy",
            service="vectorstore",
            timestamp=datetime.now().isoformat(),
            dependencies=dependencies,
            vector_store_info=vector_info
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="vectorstore",
            timestamp=datetime.now().isoformat(),
            dependencies={"error": str(e)},
            vector_store_info={}
        )

@app.post("/add-document")
async def add_document(request: DocumentRequest):
    """Добавление документа в векторное хранилище"""
    start_time = time.time()
    
    try:
        logger.info(f"📄 Добавление документа: {request.text[:50]}...")
        
        # Создаем команду для добавления документа
        command = AddDocumentCommand(
            text=request.text,
            metadata=request.metadata,
            embedding=request.embedding
        )
        
        # Отправляем команду через шину команд
        result = await command_bus.handle(command)
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "document_id": result.document_id,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления документа: {e}")
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.post("/add-documents-batch")
async def add_documents_batch(requests: List[DocumentRequest]):
    """Добавление множества документов в векторное хранилище"""
    start_time = time.time()
    
    try:
        logger.info(f"📄 Добавление {len(requests)} документов...")
        
        added_count = 0
        errors = []
        
        # Подготавливаем документы для batch обработки
        documents = []
        for request in requests:
            document = VectorDocument(
                id=None,
                text=request.text,
                metadata=request.metadata or {},
                created_at=datetime.now()
            )
            documents.append(document)
        
        # Добавляем все документы batch'ом
        try:
            doc_ids = vector_repository.add_documents_batch(documents)
            added_count = len(doc_ids)
            logger.info(f"✅ Добавлено {added_count} документов batch'ом")
        except Exception as e:
            logger.error(f"❌ Ошибка batch добавления: {e}")
            errors.append(f"Batch error: {str(e)}")
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "added_count": added_count,
            "total_count": len(requests),
            "errors": errors,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка batch добавления документов: {e}")
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.post("/remove-excluded-documents")
async def remove_excluded_documents():
    """Удаление документов с 'исключен' из базы"""
    start_time = time.time()
    try:
        logger.info("🗑️ Удаление документов с 'исключен'...")
        
        def filter_excluded(doc):
            return "исключен" in doc.text.lower() or "материал исключен" in doc.text.lower()
        
        removed_count = vector_repository.remove_documents_by_filter(filter_excluded)
        
        processing_time = time.time() - start_time
        return {
            "success": True,
            "removed_count": removed_count,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Ошибка удаления документов: {e}")
        processing_time = time.time() - start_time
        return {
            "success": False,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Поиск документов в векторном хранилище"""
    start_time = time.time()
    
    try:
        if vector_repository is None:
            raise HTTPException(status_code=503, detail="Vector repository not initialized")
        
        # Выполняем поиск напрямую через FAISS
        results = vector_repository.search_documents(request.query, request.top_k, request.threshold)
        
        processing_time = time.time() - start_time
        
        # Преобразуем результаты в формат ответа
        search_results = []
        for result in results:
            # В FAISS большее значение score = лучшая релевантность
            # Но мы хотим меньшие значения для лучшей релевантности
            relevance_score = 1.0 - result.relevance_score
            
            search_results.append(SearchResult(
                text=result.document.text,
                relevance_score=relevance_score,
                metadata=result.document.metadata or {}  # FAISS не хранит метаданные, поэтому пустой словарь
            ))
        
        return SearchResponse(
            success=True,
            results=search_results,
            total_found=len(search_results),
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=None
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Ошибка поиска документов: {e}")
        
        return SearchResponse(
            success=False,
            results=[],
            total_found=0,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            error=str(e)
        )

@app.get("/documents/count")
async def get_documents_count():
    """Получение количества документов в хранилище"""
    try:
        count = vector_repository.get_documents_count()
        
        return {
            "success": True,
            "count": count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting documents count: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Получение документа по ID"""
    try:
        document = vector_repository.get_document(document_id)
        
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "document": {
                "id": document.id,
                "text": document.text,
                "metadata": document.metadata,
                "created_at": document.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Удаление документа"""
    try:
        success = vector_repository.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "message": f"Document {document_id} deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reindex")
async def reindex_documents():
    """Переиндексация всех документов"""
    try:
        logger.info("🔄 Начало переиндексации документов...")
        
        start_time = time.time()
        result = vector_repository.reindex()
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "message": "Reindexing completed successfully",
            "documents_processed": len(vector_repository.documents),
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error reindexing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Получение статистики векторного хранилища"""
    try:
        stats = vector_repository.get_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-all")
async def clear_all_documents():
    """Очистка всех документов"""
    try:
        logger.info("🗑️ Очистка всех документов...")
        
        # Очищаем все документы
        vector_repository.clear_all()
        
        return {
            "success": True,
            "message": "All documents cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing all documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 