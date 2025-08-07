"""
Доменный сервис для обработки запросов в Request Processor Service
"""
import time
import logging
from typing import List, Optional, Dict, Any
import aiohttp
import asyncio

from ..entities.request import Request
from ..repositories.request_repository import RequestRepository

logger = logging.getLogger(__name__)


class RequestService:
    """Доменный сервис для обработки запросов"""
    
    def __init__(self, request_repository: RequestRepository):
        self.request_repository = request_repository
        self.ai_model_url = "http://ai-model:8003"
        self.vectorstore_url = "http://vectorstore:8002"
        self.payment_url = "http://payment:8005"
    
    async def process_request(self, query: str, user_id: str = None, session_id: str = None, services: List[str] = None) -> Dict[str, Any]:
        """Обработать запрос"""
        start_time = time.time()
        
        try:
            # Создаем запрос
            request = Request(
                id=None,
                query=query,
                user_id=user_id,
                session_id=session_id,
                status="processing"
            )
            
            # Сохраняем запрос
            request_id = self.request_repository.save_request(request)
            logger.info(f"Создан запрос: {request_id}")
            
            # Обрабатываем запрос через сервисы
            results = {}
            
            if services is None or "ai-model" in services:
                try:
                    ai_result = await self._call_ai_model(query)
                    results["ai-model"] = ai_result
                except Exception as e:
                    logger.error(f"Ошибка AI Model Service: {e}")
                    results["ai-model"] = {"error": str(e)}
            
            if services is None or "vectorstore" in services:
                try:
                    vector_result = await self._call_vectorstore(query)
                    results["vectorstore"] = vector_result
                except Exception as e:
                    logger.error(f"Ошибка Vector Store Service: {e}")
                    results["vectorstore"] = {"error": str(e)}
            
            if services is None or "payment" in services:
                try:
                    payment_result = await self._call_payment(user_id)
                    results["payment"] = payment_result
                except Exception as e:
                    logger.error(f"Ошибка Payment Service: {e}")
                    results["payment"] = {"error": str(e)}
            
            # Обновляем результаты
            processing_time = time.time() - start_time
            self.request_repository.update_request_results(request_id, results)
            self.request_repository.update_request_status(request_id, "completed")
            
            logger.info(f"Запрос {request_id} обработан за {processing_time:.2f}с")
            
            return {
                "request_id": request_id,
                "results": results,
                "processing_time": processing_time,
                "status": "completed"
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Ошибка обработки запроса: {e}")
            
            if 'request_id' in locals():
                self.request_repository.update_request_status(request_id, "failed")
            
            return {
                "error": str(e),
                "processing_time": processing_time,
                "status": "failed"
            }
    
    async def _call_ai_model(self, query: str) -> Dict[str, Any]:
        """Вызвать AI Model Service"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.ai_model_url}/generate",
                json={
                    "query": query,
                    "model_id": "qwen-model_full",
                    "max_length": 512,
                    "temperature": 0.7
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"AI Model Service error: {response.status}")
    
    async def _call_vectorstore(self, query: str) -> Dict[str, Any]:
        """Вызвать Vector Store Service"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.vectorstore_url}/search",
                json={
                    "query": query,
                    "top_k": 5,
                    "threshold": 0.3
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Vector Store Service error: {response.status}")
    
    async def _call_payment(self, user_id: str) -> Dict[str, Any]:
        """Вызвать Payment Service"""
        if not user_id:
            return {"status": "no_user_id"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.payment_url}/user/{user_id}/subscription") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Payment Service error: {response.status}")
    
    def get_request(self, request_id: str) -> Optional[Request]:
        """Получить запрос по ID"""
        return self.request_repository.get_request(request_id)
    
    def get_user_requests(self, user_id: str, limit: int = 10) -> List[Request]:
        """Получить запросы пользователя"""
        return self.request_repository.get_user_requests(user_id, limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        return self.request_repository.get_statistics()
    
    def delete_request(self, request_id: str) -> bool:
        """Удалить запрос"""
        return self.request_repository.delete_request(request_id)
