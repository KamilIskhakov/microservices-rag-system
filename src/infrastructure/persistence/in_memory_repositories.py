"""
In-Memory реализации репозиториев для быстрого запуска
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from src.domain.repositories.request_repository import RequestRepository
from src.domain.repositories.scraper_repository import ScraperRepository
from src.domain.repositories.vector_repository import VectorRepository
from src.domain.repositories.payment_repository import PaymentRepository
from src.domain.entities.request import Request
from src.domain.entities.scraped_data import ScrapedData, ScrapingJob
from src.domain.entities.vector_document import VectorDocument, SearchResult
from src.domain.entities.payment import Payment, Subscription


class InMemoryRequestRepository(RequestRepository):
    """In-Memory реализация репозитория запросов"""
    
    def __init__(self):
        self.requests: Dict[str, Request] = {}
        self.user_requests: Dict[str, List[str]] = defaultdict(list)
    
    def save_request(self, request: Request) -> str:
        """Сохранение запроса"""
        request_id = str(uuid.uuid4())
        request.id = request_id
        self.requests[request_id] = request
        
        if request.user_id:
            self.user_requests[request.user_id].append(request_id)
        
        return request_id
    
    def get_request(self, request_id: str) -> Optional[Request]:
        """Получение запроса по ID"""
        return self.requests.get(request_id)
    
    def update_request_status(self, request_id: str, status: str) -> bool:
        """Обновление статуса запроса"""
        if request_id in self.requests:
            self.requests[request_id].status = status
            return True
        return False
    
    def get_user_requests(self, user_id: str) -> List[Request]:
        """Получение запросов пользователя"""
        request_ids = self.user_requests.get(user_id, [])
        return [self.requests[req_id] for req_id in request_ids if req_id in self.requests]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        total_requests = len(self.requests)
        pending_requests = len([r for r in self.requests.values() if r.status == "pending"])
        completed_requests = len([r for r in self.requests.values() if r.status == "completed"])
        
        return {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "completed_requests": completed_requests,
            "unique_users": len(self.user_requests)
        }
    
    # Реализация методов базового интерфейса
    def save(self, entity: Request) -> str:
        """Сохранение запроса (алиас для save_request)"""
        return self.save_request(entity)
    
    def get_by_id(self, entity_id: str) -> Optional[Request]:
        """Получение запроса по ID (алиас для get_request)"""
        return self.get_request(entity_id)
    
    def get_all(self) -> List[Request]:
        """Получение всех запросов"""
        return list(self.requests.values())
    
    def delete(self, entity_id: str) -> bool:
        """Удаление запроса"""
        if entity_id in self.requests:
            del self.requests[entity_id]
            return True
        return False
    
    def update(self, entity_id: str, entity: Request) -> bool:
        """Обновление запроса"""
        if entity_id in self.requests:
            entity.id = entity_id
            self.requests[entity_id] = entity
            return True
        return False
    """In-Memory реализация репозитория запросов"""
    
    def __init__(self):
        self.requests: Dict[str, Request] = {}
        self.user_requests: Dict[str, List[str]] = defaultdict(list)
    
    def save_request(self, request: Request) -> str:
        """Сохранение запроса"""
        request_id = str(uuid.uuid4())
        request.id = request_id
        self.requests[request_id] = request
        
        if request.user_id:
            self.user_requests[request.user_id].append(request_id)
        
        return request_id
    
    def get_request(self, request_id: str) -> Optional[Request]:
        """Получение запроса по ID"""
        return self.requests.get(request_id)
    
    def update_request_status(self, request_id: str, status: str) -> bool:
        """Обновление статуса запроса"""
        if request_id in self.requests:
            self.requests[request_id].status = status
            return True
        return False
    
    def get_user_requests(self, user_id: str) -> List[Request]:
        """Получение запросов пользователя"""
        request_ids = self.user_requests.get(user_id, [])
        return [self.requests[req_id] for req_id in request_ids if req_id in self.requests]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        total_requests = len(self.requests)
        pending_requests = len([r for r in self.requests.values() if r.status == "pending"])
        completed_requests = len([r for r in self.requests.values() if r.status == "completed"])
        
        return {
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "completed_requests": completed_requests,
            "unique_users": len(self.user_requests)
        }


class InMemoryScraperRepository(ScraperRepository):
    """In-Memory реализация репозитория скрапера"""
    
    def __init__(self):
        self.jobs: Dict[str, ScrapingJob] = {}
        self.data: List[ScrapedData] = []
    
    def save_job(self, job: ScrapingJob) -> str:
        """Сохранение задачи парсинга"""
        job_id = str(uuid.uuid4())
        job.job_id = job_id
        job.created_at = datetime.now()
        self.jobs[job_id] = job
        return job_id
    
    def get_job(self, job_id: str) -> Optional[ScrapingJob]:
        """Получение задачи по ID"""
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: str, progress: float = 0.0) -> bool:
        """Обновление статуса задачи"""
        if job_id in self.jobs:
            self.jobs[job_id].status = status
            self.jobs[job_id].progress = progress
            if status == "completed":
                self.jobs[job_id].completed_at = datetime.now()
            return True
        return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Отмена задачи"""
        return self.update_job_status(job_id, "cancelled")
    
    def get_all_jobs(self) -> List[ScrapingJob]:
        """Получение всех задач"""
        return list(self.jobs.values())
    
    def save_data(self, data: ScrapedData) -> str:
        """Сохранение данных"""
        data_id = str(uuid.uuid4())
        data.id = data_id
        data.created_at = datetime.now()
        self.data.append(data)
        return data_id
    
    def get_latest_data(self, limit: int = 100) -> List[ScrapedData]:
        """Получение последних данных"""
        return sorted(self.data, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def get_data_count(self) -> int:
        """Получение количества данных"""
        return len(self.data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        total_jobs = len(self.jobs)
        active_jobs = len([j for j in self.jobs.values() if j.status == "running"])
        completed_jobs = len([j for j in self.jobs.values() if j.status == "completed"])
        
        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "total_data": len(self.data)
        }
    
    # Реализация методов базового интерфейса
    def save(self, entity: ScrapedData) -> str:
        """Сохранение данных (алиас для save_data)"""
        return self.save_data(entity)
    
    def get_by_id(self, entity_id: str) -> Optional[ScrapedData]:
        """Получение данных по ID"""
        for data in self.data:
            if data.id == entity_id:
                return data
        return None
    
    def get_all(self) -> List[ScrapedData]:
        """Получение всех данных"""
        return self.data.copy()
    
    def delete(self, entity_id: str) -> bool:
        """Удаление данных"""
        for i, data in enumerate(self.data):
            if data.id == entity_id:
                del self.data[i]
                return True
        return False
    
    def update(self, entity_id: str, entity: ScrapedData) -> bool:
        """Обновление данных"""
        for i, data in enumerate(self.data):
            if data.id == entity_id:
                entity.id = entity_id
                self.data[i] = entity
                return True
        return False


class InMemoryVectorRepository(VectorRepository):
    """In-Memory реализация репозитория векторного хранилища"""
    
    def __init__(self):
        self.documents: Dict[str, VectorDocument] = {}
        self.embeddings: Dict[str, List[float]] = {}
    
    def add_document(self, document: VectorDocument) -> str:
        """Добавление документа"""
        doc_id = str(uuid.uuid4())
        document.id = doc_id
        document.created_at = datetime.now()
        self.documents[doc_id] = document
        
        if document.embedding:
            self.embeddings[doc_id] = document.embedding
        
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[VectorDocument]:
        """Получение документа по ID"""
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Удаление документа"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            if doc_id in self.embeddings:
                del self.embeddings[doc_id]
            return True
        return False
    
    def search_documents(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[SearchResult]:
        """Поиск документов (улучшенная заглушка)"""
        # Приводим запрос к нижнему регистру для единообразия
        query_lower = query.lower()
        
        # Улучшенная логика поиска
        results = []
        rank = 0
        for doc_id, doc in self.documents.items():
            doc_text_lower = doc.text.lower()
            
            # Проверяем различные типы совпадений
            score = 0.0
            matched = False
            
            # Точное совпадение фразы (только для длинных запросов)
            if len(query_lower) > 10 and query_lower in doc_text_lower:
                score = 0.1  # Очень хорошая релевантность
                matched = True
            
            # Совпадение отдельных слов (включая короткие значимые слова)
            query_words = [word for word in query_lower.split() if len(word) > 2]  # Игнорируем только очень короткие слова
            doc_words = doc_text_lower.split()
            
            if len(query_words) > 0:
                # Считаем количество совпадающих слов
                matches = sum(1 for word in query_words if word in doc_words)
                if matches >= len(query_words) * 0.3:  # Минимум 30% слов должны совпадать
                    # Чем больше совпадений, тем лучше релевантность
                    word_score = 0.1 + (0.8 * (1 - matches / len(query_words)))
                    score = min(score, word_score) if score > 0 else word_score
                    matched = True
            
            if matched:
                results.append(SearchResult(
                    document=doc,
                    relevance_score=score,
                    rank=rank
                ))
                rank += 1
        
        return sorted(results, key=lambda x: x.relevance_score)[:top_k]  # Сортируем по возрастанию (лучшие первые)
    
    def reindex(self) -> bool:
        """Переиндексация (заглушка)"""
        return True
    
    def get_documents_count(self) -> int:
        """Получение количества документов"""
        return len(self.documents)
    
    def get_info(self) -> Dict[str, Any]:
        """Получение информации о хранилище"""
        return {
            "documents_count": len(self.documents),
            "embeddings_count": len(self.embeddings),
            "index_type": "in-memory"
        }
    
    def clear_all(self):
        """Очистка всех документов"""
        self.documents.clear()
        self.embeddings.clear()
        print("All documents cleared from in-memory repository")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        return {
            "total_documents": len(self.documents),
            "total_embeddings": len(self.embeddings),
            "index_size_mb": 0.0
        }
    
    # Реализация методов базового интерфейса
    def save(self, entity: VectorDocument) -> str:
        """Сохранение документа (алиас для add_document)"""
        return self.add_document(entity)
    
    def get_by_id(self, entity_id: str) -> Optional[VectorDocument]:
        """Получение документа по ID (алиас для get_document)"""
        return self.get_document(entity_id)
    
    def get_all(self) -> List[VectorDocument]:
        """Получение всех документов"""
        return list(self.documents.values())
    
    def delete(self, entity_id: str) -> bool:
        """Удаление документа (алиас для delete_document)"""
        return self.delete_document(entity_id)
    
    def update(self, entity_id: str, entity: VectorDocument) -> bool:
        """Обновление документа"""
        if entity_id in self.documents:
            entity.id = entity_id
            self.documents[entity_id] = entity
            return True
        return False


class InMemoryPaymentRepository(PaymentRepository):
    """In-Memory реализация репозитория платежей"""
    
    def __init__(self):
        self.payments: Dict[str, Payment] = {}
        self.subscriptions: Dict[str, Subscription] = {}
        self.user_payments: Dict[str, List[str]] = defaultdict(list)
        self.user_subscriptions: Dict[str, List[str]] = defaultdict(list)
    
    def save_payment(self, payment: Payment) -> str:
        """Сохранение платежа"""
        payment_id = str(uuid.uuid4())
        payment.payment_id = payment_id
        payment.created_at = datetime.now()
        self.payments[payment_id] = payment
        
        self.user_payments[payment.user_id].append(payment_id)
        return payment_id
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Получение платежа по ID"""
        return self.payments.get(payment_id)
    
    def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Обновление статуса платежа"""
        if payment_id in self.payments:
            self.payments[payment_id].status = status
            self.payments[payment_id].updated_at = datetime.now()
            return True
        return False
    
    def get_user_payments(self, user_id: str) -> List[Payment]:
        """Получение платежей пользователя"""
        payment_ids = self.user_payments.get(user_id, [])
        return [self.payments[pay_id] for pay_id in payment_ids if pay_id in self.payments]
    
    def save_subscription(self, subscription: Subscription) -> str:
        """Сохранение подписки"""
        sub_id = str(uuid.uuid4())
        subscription.subscription_id = sub_id
        subscription.created_at = datetime.now()
        self.subscriptions[sub_id] = subscription
        
        self.user_subscriptions[subscription.user_id].append(sub_id)
        return sub_id
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Получение подписки по ID"""
        return self.subscriptions.get(subscription_id)
    
    def update_subscription_status(self, subscription_id: str, status: str) -> bool:
        """Обновление статуса подписки"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].status = status
            self.subscriptions[subscription_id].updated_at = datetime.now()
            return True
        return False
    
    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """Получение активной подписки пользователя"""
        sub_ids = self.user_subscriptions.get(user_id, [])
        for sub_id in sub_ids:
            if sub_id in self.subscriptions:
                sub = self.subscriptions[sub_id]
                if sub.status == "active":
                    return sub
        return None
    
    # Реализация методов базового интерфейса
    def save(self, entity: Payment) -> str:
        """Сохранение платежа (алиас для save_payment)"""
        return self.save_payment(entity)
    
    def get_by_id(self, entity_id: str) -> Optional[Payment]:
        """Получение платежа по ID (алиас для get_payment)"""
        return self.get_payment(entity_id)
    
    def get_all(self) -> List[Payment]:
        """Получение всех платежей"""
        return list(self.payments.values())
    
    def delete(self, entity_id: str) -> bool:
        """Удаление платежа"""
        if entity_id in self.payments:
            del self.payments[entity_id]
            return True
        return False
    
    def update(self, entity_id: str, entity: Payment) -> bool:
        """Обновление платежа"""
        if entity_id in self.payments:
            entity.payment_id = entity_id
            self.payments[entity_id] = entity
            return True
        return False 