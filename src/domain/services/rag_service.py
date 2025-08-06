import threading
import time
from typing import List, Optional
from dataclasses import dataclass

from src.domain.entities.model import Model
from src.domain.repositories.model_repository import ModelRepository
from src.domain.strategies.model_loading_strategy import ModelLoadingStrategy
from src.shared.utils.logger import logger

@dataclass
class CheckRequest:
    """Запрос на проверку"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class CheckResponse:
    """Ответ на проверку"""
    result: str
    processing_time: float
    device_info: dict
    confidence: float = 0.0
    extremist_reason: str = ""
    court_date: str = ""
    court_name: str = ""
    material_name: str = ""

@dataclass
class SearchResult:
    """Результат поиска"""
    text: str
    relevance_score: float
    metadata: dict = None

class RAGService:
    """Оптимизированный RAG сервис с многопоточностью"""
    
    def __init__(self, model_repository: ModelRepository, vector_store):
        logger.info("Initializing RAG service...")
        self.model_repository = model_repository
        self.vector_store = vector_store
    
        self._lock = threading.Lock()
        self._request_count = 0
        self._total_processing_time = 0.0
        
        # Пороговые значения для определения экстремистских материалов
        self.relevance_threshold = 0.3
        self.confidence_threshold = 0.7

        self._load_vector_store()
        logger.info(f"RAG service initialized")
    
    def _load_vector_store(self):
        """Загружает векторное хранилище"""
        try:
            self.vector_store.load()
            logger.info("Vector store loaded successfully")
        except Exception as e:
            logger.warning(f"Error loading vector store: {e}")
            self.vector_store.texts = []
    
    def _is_extremist_material(self, search_results: List[SearchResult]) -> bool:
        """Определяет, является ли материал экстремистским на основе релевантности"""
        if not search_results:
            return False
        
        # Проверяем, есть ли высокорелевантные результаты
        high_relevance_results = [
            result for result in search_results 
            if result.relevance_score <= self.relevance_threshold
        ]
        
        logger.info(f"Relevance threshold: {self.relevance_threshold}")
        logger.info(f"Best result score: {search_results[0].relevance_score}")
        logger.info(f"High relevance results count: {len(high_relevance_results)}")
        
        # Дополнительная проверка: если лучший результат имеет слишком низкую релевантность,
        # считаем что материал не найден
        if search_results[0].relevance_score > 0.8:
            logger.info(f"Best result score {search_results[0].relevance_score} too high, rejecting")
            return False
        
        if len(high_relevance_results) == 0 and search_results[0].relevance_score > 0.8:
            logger.info(f"No high-relevance results and best score {search_results[0].relevance_score} too high")
            return False
        
        if high_relevance_results:
            logger.info(f"Found {len(high_relevance_results)} high-relevance results")
            return True
        
        return False
    
    def _extract_court_info(self, search_results: List[SearchResult]) -> tuple:
        """Извлекает информацию о судебном решении из результатов поиска"""
        if not search_results:
            return "", "", ""
        
        best_result = search_results[0]
        metadata = best_result.metadata or {}
        
        court_date = metadata.get('court_date', '')
        court_name = metadata.get('court_name', '')
        material_name = metadata.get('material_name', '')
        
        return court_date, court_name, material_name
    
    def check(self, request: CheckRequest) -> CheckResponse:
        """Основной метод проверки текста"""
        start_time = time.time()
        
        try:
            with self._lock:
                self._request_count += 1
            
            logger.info(f"Processing request {self._request_count}: {request.query[:50]}...")
            
            # Поиск релевантных документов
            search_results = self._search_relevant_documents(request.query)
            
            # Определение экстремистского характера
            is_extremist = self._is_extremist_material(search_results)
            
            # Извлечение информации о суде
            court_date, court_name, material_name = self._extract_court_info(search_results)
            
            # Формирование ответа
            if is_extremist:
                result = "ЭКСТРЕМИСТСКИЙ МАТЕРИАЛ"
                extremist_reason = f"Найден в реестре с релевантностью {search_results[0].relevance_score:.3f}"
            else:
                result = "НЕ ЭКСТРЕМИСТСКИЙ МАТЕРИАЛ"
                extremist_reason = "Не найден в реестре экстремистских материалов"
            
            processing_time = time.time() - start_time
            self._update_statistics(processing_time)
            
            return CheckResponse(
                result=result,
                processing_time=processing_time,
                device_info={"device": "cpu", "framework": "torch"},
                confidence=1.0 - (search_results[0].relevance_score if search_results else 1.0),
                extremist_reason=extremist_reason,
                court_date=court_date,
                court_name=court_name,
                material_name=material_name
            )
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            processing_time = time.time() - start_time
            return CheckResponse(
                result="ОШИБКА ОБРАБОТКИ",
                processing_time=processing_time,
                device_info={"device": "cpu", "framework": "torch"},
                extremist_reason=f"Ошибка: {str(e)}"
            )
    
    def _search_relevant_documents(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Поиск релевантных документов"""
        try:
            # Здесь должна быть логика поиска в векторном хранилище
            # Пока возвращаем заглушку
            return [
                SearchResult(
                    text="Тестовый документ",
                    relevance_score=0.5,
                    metadata={
                        'court_date': '2023-01-01',
                        'court_name': 'Тестовый суд',
                        'material_name': 'Тестовый материал'
                    }
                )
            ]
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _update_statistics(self, processing_time: float):
        """Обновляет статистику обработки"""
        with self._lock:
            self._total_processing_time += processing_time
    
    def get_statistics(self) -> dict:
        """Возвращает статистику сервиса"""
        with self._lock:
            avg_time = self._total_processing_time / max(self._request_count, 1)
        
        return {
            "total_requests": self._request_count,
            "average_processing_time": avg_time,
            "total_processing_time": self._total_processing_time
        }
    
    def cleanup(self):
        """Очистка ресурсов"""
        logger.info("Cleaning up RAG service...")
    
    def get_health_status(self) -> dict:
        """Проверка здоровья сервиса"""
        try:
            model_loaded = self.model_repository.get_model() is not None
            vector_store_loaded = self.vector_store is not None
            
            return {
                "status": "healthy" if model_loaded and vector_store_loaded else "unhealthy",
                "model_loaded": model_loaded,
                "vector_store_loaded": vector_store_loaded,
                "statistics": self.get_statistics()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)} 