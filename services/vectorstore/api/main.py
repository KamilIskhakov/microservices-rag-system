"""
Vector Store Service API - полностью независимый микросервис
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Добавляем путь к доменной логике
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импорты доменной логики
from domain.services.vector_service import VectorService
from infrastructure.persistence.optimized_faiss_repository import OptimizedFAISSRepository

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vector Store Service", version="2.0.0")

# Глобальные переменные
vector_service: Optional[VectorService] = None

# Конфигурация из переменных окружения
MODEL_NAME = os.getenv("VECTOR_STORE_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.3"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))


class DocumentRequest(BaseModel):
    """Запрос для добавления документа"""
    content: str
    metadata: Dict[str, Any] = {}


class SearchRequest(BaseModel):
    """Запрос для поиска"""
    query: str
    top_k: int = TOP_K_RESULTS
    threshold: float = RELEVANCE_THRESHOLD


class SearchResponse(BaseModel):
    """Ответ на поиск"""
    success: bool
    results: List[Dict[str, Any]]
    processing_time: float
    timestamp: str
    query: str
    total_results: int
    error: Optional[str] = None


class DocumentResponse(BaseModel):
    """Ответ для документа"""
    success: bool
    document_id: str
    processing_time: float
    timestamp: str
    error: Optional[str] = None


class StatisticsResponse(BaseModel):
    """Ответ со статистикой"""
    total_documents: int
    indexed_documents: int
    index_size: int
    embedding_dimension: int
    model_name: str


@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    global vector_service
    
    try:
        logger.info("🚀 Инициализация Vector Store Service...")
        
        # Инициализируем репозиторий
        vector_repository = OptimizedFAISSRepository(model_name=MODEL_NAME)
        
        # Инициализируем доменный сервис
        vector_service = VectorService(vector_repository, MODEL_NAME)
        
        logger.info("✅ Vector Store Service готов к работе")
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Vector Store Service: {e}")
        raise


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        if vector_service is None:
            return {"status": "unhealthy", "error": "Service not initialized"}
        
        # Проверяем доступность сервиса
        stats = await vector_service.get_statistics()
        
        return {
            "status": "healthy",
            "service": "vectorstore",
            "timestamp": datetime.now().isoformat(),
            "total_documents": stats.get("total_documents", 0),
            "indexed_documents": stats.get("index_size", 0)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.post("/add-document", response_model=DocumentResponse)
async def add_document(request: DocumentRequest):
    """Добавить документ"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Добавляем документ: {request.content[:50]}...")
        
        # Добавляем документ
        document_id = vector_service.add_document(
            content=request.content,
            metadata=request.metadata
        )
        
        processing_time = time.time() - start_time
        
        return DocumentResponse(
            success=True,
            document_id=document_id,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Ошибка добавления документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/add-documents")
async def add_documents(documents: List[DocumentRequest]):
    """Добавить несколько документов"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Добавляем {len(documents)} документов...")
        
        # Подготавливаем данные для добавления
        docs_data = []
        for doc in documents:
            docs_data.append({
                "content": doc.content,
                "metadata": doc.metadata
            })
        
        # Добавляем документы
        document_ids = vector_service.add_documents(docs_data)
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "document_ids": document_ids,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "total_added": len(document_ids)
        }
        
    except Exception as e:
        logger.error(f"Ошибка добавления документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Поиск документов"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Поиск: {request.query[:50]}...")
        
        # Выполняем поиск
        results = await vector_service.search_similar(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        # Преобразуем результаты в словари
        results_data = []
        logger.info(f"Преобразуем {len(results)} результатов поиска")
        
        for i, result in enumerate(results):
            try:
                result_dict = {
                    "document_id": result.document_id,
                    "content": result.content,
                    "relevance_score": result.relevance_score,
                    "distance": result.distance,
                    "metadata": result.metadata
                }
                results_data.append(result_dict)
            except Exception as e:
                logger.error(f"Ошибка преобразования результата {i}: {e}")
                logger.error(f"Тип результата: {type(result)}")
                logger.error(f"Атрибуты результата: {dir(result)}")
                raise
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            success=True,
            results=results_data,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            query=request.query,
            total_results=len(results_data)
        )
        
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/document/{document_id}")
async def get_document(document_id: str):
    """Получить документ по ID"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        document = vector_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "id": document.id,
            "content": document.content,
            "metadata": document.metadata,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "is_indexed": document.is_indexed()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/document/{document_id}")
async def update_document(document_id: str, request: DocumentRequest):
    """Обновить документ"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        start_time = time.time()
        
        logger.info(f"Обновляем документ: {document_id}")
        
        # Обновляем документ
        success = vector_service.update_document(
            document_id=document_id,
            content=request.content,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        processing_time = time.time() - start_time
        
        return DocumentResponse(
            success=True,
            document_id=document_id,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """Удалить документ"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        logger.info(f"Удаляем документ: {document_id}")
        
        # Удаляем документ
        success = vector_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "document_id": document_id,
            "message": "Document deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def get_all_documents():
    """Получить все документы"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        documents = vector_service.get_all_documents()
        
        result = []
        for doc in documents:
            result.append({
                "id": doc.id,
                "content": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content,
                "metadata": doc.metadata,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "is_indexed": doc.is_indexed()
            })
        
        return {
            "documents": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Получить статистику"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        stats = vector_service.get_statistics()
        
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model-info")
async def get_model_info():
    """Получить информацию о модели"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        return vector_service.get_model_info()
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear-index")
async def clear_index():
    """Очистить индекс"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        logger.info("Очищаем индекс...")
        
        success = vector_service.clear_index()
        
        return {
            "success": success,
            "message": "Index cleared successfully" if success else "Failed to clear index"
        }
        
    except Exception as e:
        logger.error(f"Ошибка очистки индекса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rebuild-index")
async def rebuild_index():
    """Перестроить индекс"""
    try:
        if vector_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        logger.info("Перестраиваем индекс...")
        
        success = vector_service.rebuild_index()
        
        return {
            "success": success,
            "message": "Index rebuilt successfully" if success else "Failed to rebuild index"
        }
        
    except Exception as e:
        logger.error(f"Ошибка перестроения индекса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
