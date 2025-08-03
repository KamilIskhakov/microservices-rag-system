import threading
import time
from typing import List, Optional
from dataclasses import dataclass

from .model_manager import ModelManager
from .prompt_manager import PromptManager, SearchResult, StructuredResponse
from .device_factory import DeviceManager
from .logger import logger
from vectorstore.faiss_store import FaissStore
from config import settings

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
    extremist_reason: str = ""  # Добавляем поле для причины
    court_date: str = ""  # Дата судебного решения
    court_name: str = ""  # Название суда
    material_name: str = ""  # Наименование материала

class RAGService:
    """Оптимизированный RAG сервис с многопоточностью"""
    
    def __init__(self):
        logger.info("Initializing RAG service...")
        self.model_manager = ModelManager(settings.QWEN_MODEL_PATH)
        self.prompt_manager = PromptManager()
        self.device_manager = DeviceManager()
        self.vector_store = FaissStore()
    
        self._lock = threading.Lock()
        self._request_count = 0
        self._total_processing_time = 0.0
        
        # Пороговые значения для определения экстремистских материалов
        self.relevance_threshold = 0.3  # Очень строгий порог релевантности
        self.confidence_threshold = 0.7  # Порог уверенности модели

        self._load_vector_store()

        logger.info(f"RAG service initialized on {self.model_manager.device_config.device}")
    
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
        # В FAISS меньшее значение = лучшая релевантность
        high_relevance_results = [
            result for result in search_results 
            if result.relevance_score <= self.relevance_threshold  # Меньше = лучше для FAISS
        ]
        
        logger.info(f"Relevance threshold: {self.relevance_threshold}")
        logger.info(f"Best result score: {search_results[0].relevance_score}")
        logger.info(f"High relevance results count: {len(high_relevance_results)}")
        
        # Дополнительная проверка: если лучший результат имеет слишком низкую релевантность,
        # считаем что материал не найден
        if search_results[0].relevance_score > 0.8:  # Более строгий порог
            logger.info(f"Best result score {search_results[0].relevance_score} too high, rejecting")
            return False
        
        # Дополнительная проверка: если лучший результат имеет очень низкую релевантность,
        # но есть много результатов, это может быть ложное срабатывание
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
            return "", "", "", ""
        
        # Берем самый релевантный результат
        best_result = min(search_results, key=lambda x: x.relevance_score)
        
        # Извлекаем дату из текста
        import re
        date_pattern = r'\d{1,2}\.\d{1,2}\.\d{4}'
        date_match = re.search(date_pattern, best_result.text)
        court_date = date_match.group() if date_match else ""
        
        # Извлекаем название суда
        court_patterns = [
            r'Верховный суд',
            r'Московский городской суд',
            r'Санкт-Петербургский городской суд',
            r'областной суд',
            r'краевой суд',
            r'республиканский суд',
            r'районный суд',
            r'городской суд'
        ]
        
        court_name = ""
        for pattern in court_patterns:
            court_match = re.search(pattern, best_result.text, re.IGNORECASE)
            if court_match:
                court_name = court_match.group()
                break
        
        # Сначала ищем в кавычках - это самый надежный способ
        quote_pattern = r'«([^»]+)»'
        quote_matches = re.findall(quote_pattern, best_result.text)
        if quote_matches:
            # Берем самое длинное название в кавычках
            material_name = max(quote_matches, key=len)
            # Добавляем кавычки для красоты
            material_name = f"«{material_name}»"
        else:
            # Если не нашли в кавычках, ищем по паттернам
            material_patterns = [
                r'печатная книга[^,]*',
                r'книга[^,]*',
                r'статья[^,]*',
                r'видео[^,]*',
                r'аудио[^,]*',
                r'издание[^,]*',
                r'материал[^,]*',
                r'брошюра[^,]*',
                r'печатный материал[^,]*'
            ]
            
            material_name = ""
            for pattern in material_patterns:
                material_match = re.search(pattern, best_result.text, re.IGNORECASE)
                if material_match:
                    material_name = material_match.group().strip()
                    break
        
        # Если все еще не нашли, берем первые слова до запятой
        if not material_name:
            words = best_result.text.split(',')[0].split()[:8]
            material_name = " ".join(words)
            if len(material_name) > 50:
                material_name = material_name[:50] + "..."
        
        # Извлекаем описание
        description = best_result.text
        
        return court_date, court_name, material_name, description
    
    def check(self, request: CheckRequest) -> CheckResponse:
        """Основной метод проверки с четкой логикой"""
        start_time = time.time()
        
        # Добавляем уникальный timestamp для предотвращения кеширования
        import uuid
        request_id = str(uuid.uuid4())[:8]
        
        # Приводим запрос к нижнему регистру
        normalized_query = request.query.lower()
        logger.info(f"Processing query: {request.query} -> normalized: {normalized_query} (request_id: {request_id})")
        
        # 1. Поиск релевантных документов
        search_results = self._search_relevant_documents(normalized_query)
        
        # Отладочная информация
        logger.info(f"Search results count: {len(search_results)}")
        if search_results:
            logger.info(f"Best result score: {search_results[0].relevance_score}")
            logger.info(f"Best result text: {search_results[0].text[:100]}...")
        
        # 2. Определяем, является ли материал экстремистским
        is_extremist = self._is_extremist_material(search_results)
        logger.info(f"Is extremist: {is_extremist}")
        
        # 3. Извлекаем информацию о судебном решении
        court_date, court_name, material_name, description = self._extract_court_info(search_results)
        logger.info(f"Court date: {court_date}, Court name: {court_name}, Material: {material_name}")
        
        # 4. Формируем ответ
        if is_extremist:
            result = "Да"
            confidence = 0.95
            
            # Формируем краткий ответ с названием материала и датой
            if material_name and court_date:
                extremist_reason = f"{material_name} - {court_date}"
            elif material_name:
                extremist_reason = material_name
            elif court_date:
                extremist_reason = f"Решение от {court_date}"
            else:
                extremist_reason = "Материал в реестре"
        else:
            result = "Нет"
            confidence = 0.8
            extremist_reason = ""
        
        # 5. Форматируем финальный ответ
        if result == "Да":
            final_response = f"Да. {extremist_reason}"
        else:
            final_response = "Нет"
        
        processing_time = time.time() - start_time
        self._update_statistics(processing_time)
        
        logger.request_processing(request.query, processing_time, final_response)
        
        return CheckResponse(
            result=final_response,
            processing_time=processing_time,
            device_info=self.model_manager.get_device_info(),
            confidence=confidence,
            extremist_reason=extremist_reason,
            court_date=court_date,
            court_name=court_name,
            material_name=material_name
        )
    
    def _search_relevant_documents(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Поиск релевантных документов"""
        try:
            docs_and_scores = self.vector_store.query(query)
            
            results = []
            for doc, score in docs_and_scores[:top_k]:
                results.append(SearchResult(
                    text=doc,
                    relevance_score=score,
                    metadata={"source": "faiss"}
                ))
            
            # Восстанавливаем алгоритм точного совпадения для поиска экстремистских материалов
            query_words = query.lower().split()
            exact_matches = []
            
            for i, text in enumerate(self.vector_store.texts):
                text_lower = text.lower()
                # Проверяем, содержит ли текст все слова из запроса
                if all(word in text_lower for word in query_words):
                    # Вычисляем качество совпадения на основе количества совпадающих слов
                    words_found = sum(1 for word in query_words if word in text_lower)
                    total_words = len(query_words)
                    
                    # Если найдено меньше 80% слов, пропускаем
                    if words_found < total_words * 0.8:
                        continue
                    
                    # Вычисляем релевантность на основе качества совпадения
                    relevance = 1.0 / (1.0 + words_found)  # Меньше = лучше
                    
                    exact_matches.append(SearchResult(
                        text=text,
                        relevance_score=relevance,
                        metadata={"source": "exact_match"}
                    ))
            
            # Добавляем точные совпадения в начало результатов
            if exact_matches:
                logger.info(f"Found {len(exact_matches)} exact matches")
                results = exact_matches + results
            
            logger.info(f"Found {len(results)} relevant documents for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _update_statistics(self, processing_time: float):
        """Обновляет статистику обработки"""
        with self._lock:
            self._request_count += 1
            self._total_processing_time += processing_time
    
    def get_statistics(self) -> dict:
        """Возвращает статистику сервиса"""
        with self._lock:
            avg_time = (self._total_processing_time / self._request_count 
                       if self._request_count > 0 else 0)
            
            stats = {
                "total_requests": self._request_count,
                "average_processing_time": avg_time,
                "device_info": self.model_manager.get_device_info(),
                "database_size": len(self.vector_store.texts),
                "relevance_threshold": self.relevance_threshold
            }
            
            logger.info(f"Statistics: {stats}")
            return stats
    
    def cleanup(self):
        """Очищает ресурсы"""
        logger.info("Cleaning up RAG service resources")
        self.model_manager.cleanup()
        logger.info("RAG service cleanup completed")
    
    def get_health_status(self) -> dict:
        """Возвращает статус здоровья сервиса"""
        health = {
            "status": "healthy",
            "device": self.model_manager.device_config.device,
            "model_loaded": self.model_manager._model is not None,
            "vector_store_loaded": len(self.vector_store.texts) > 0,
            "database_size": len(self.vector_store.texts),
            "statistics": self.get_statistics()
        }
        
        logger.info(f"Health status: {health}")
        return health
    
