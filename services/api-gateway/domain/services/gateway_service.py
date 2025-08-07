"""
Доменный сервис для работы с API Gateway
"""
import logging
import time
import aiohttp
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.gateway_request import GatewayRequest, ServiceEndpoint

logger = logging.getLogger(__name__)


class GatewayService:
    """Доменный сервис для работы с API Gateway"""
    
    def __init__(self):
        self.session = None
        self.services = {
            "ai-model": ServiceEndpoint("ai-model", "http://ai-model:8003"),
            "vectorstore": ServiceEndpoint("vectorstore", "http://vectorstore:8002"),
            "scraper": ServiceEndpoint("scraper", "http://scraper:8001"),
            "request-processor": ServiceEndpoint("request-processor", "http://request-processor:8004"),
            "payment": ServiceEndpoint("payment", "http://payment:8005")
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить HTTP сессию"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def route_request(self, method: str, path: str, headers: Dict[str, str] = None, body: Dict[str, Any] = None, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """Маршрутизировать запрос к соответствующему сервису"""
        start_time = time.time()
        
        # Создаем запрос
        gateway_request = GatewayRequest(
            id=None,
            method=method,
            path=path,
            user_id=user_id,
            session_id=session_id,
            headers=headers,
            body=body
        )
        
        try:
            # Определяем целевой сервис
            target_service = self._determine_target_service(path)
            if not target_service:
                raise ValueError(f"Неизвестный путь: {path}")
            
            # Проверяем доступность сервиса
            if not self.services[target_service].is_available:
                raise Exception(f"Сервис {target_service} недоступен")
            
            # Формируем URL для запроса
            service_url = self.services[target_service].url
            target_url = f"{service_url}{path}"
            
            logger.info(f"Маршрутизируем запрос {method} {path} к сервису {target_service}")
            
            # Выполняем запрос
            response = await self._make_request(method, target_url, headers, body)
            
            # Обновляем запрос
            processing_time = time.time() - start_time
            gateway_request.set_response(response["status_code"], response["body"])
            gateway_request.set_processing_time(processing_time)
            
            logger.info(f"Запрос {gateway_request.id} обработан за {processing_time:.3f}с")
            
            return {
                "success": True,
                "request_id": gateway_request.id,
                "target_service": target_service,
                "status_code": response["status_code"],
                "body": response["body"],
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            gateway_request.set_error(str(e))
            gateway_request.set_processing_time(processing_time)
            
            logger.error(f"Ошибка маршрутизации запроса: {e}")
            
            return {
                "success": False,
                "request_id": gateway_request.id,
                "error": str(e),
                "processing_time": processing_time
            }
    
    def _determine_target_service(self, path: str) -> Optional[str]:
        """Определить целевой сервис по пути"""
        if path.startswith("/ai-model") or path.startswith("/generate") or path.startswith("/model"):
            return "ai-model"
        elif path.startswith("/vectorstore") or path.startswith("/search") or path.startswith("/document"):
            return "vectorstore"
        elif path.startswith("/scraper") or path.startswith("/job") or path.startswith("/data"):
            return "scraper"
        elif path.startswith("/request-processor") or path.startswith("/process"):
            return "request-processor"
        elif path.startswith("/payment") or path.startswith("/subscription"):
            return "payment"
        else:
            return None
    
    async def _make_request(self, method: str, url: str, headers: Dict[str, str] = None, body: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполнить HTTP запрос"""
        session = await self._get_session()
        
        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    response_body = await response.json()
                    return {
                        "status_code": response.status,
                        "body": response_body
                    }
            elif method.upper() == "POST":
                async with session.post(url, headers=headers, json=body) as response:
                    response_body = await response.json()
                    return {
                        "status_code": response.status,
                        "body": response_body
                    }
            elif method.upper() == "PUT":
                async with session.put(url, headers=headers, json=body) as response:
                    response_body = await response.json()
                    return {
                        "status_code": response.status,
                        "body": response_body
                    }
            elif method.upper() == "DELETE":
                async with session.delete(url, headers=headers) as response:
                    response_body = await response.json()
                    return {
                        "status_code": response.status,
                        "body": response_body
                    }
            else:
                raise ValueError(f"Неподдерживаемый метод: {method}")
                
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса {method} {url}: {e}")
            raise
    
    async def check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Проверить здоровье сервиса"""
        if service_name not in self.services:
            return {"error": f"Сервис {service_name} не найден"}
        
        service = self.services[service_name]
        start_time = time.time()
        
        try:
            session = await self._get_session()
            health_url = f"{service.url}{service.health_check_path}"
            
            async with session.get(health_url, timeout=5) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    health_data = await response.json()
                    service.update_health(True, response_time)
                    
                    return {
                        "service": service_name,
                        "status": "healthy",
                        "response_time": response_time,
                        "data": health_data
                    }
                else:
                    service.update_health(False, response_time)
                    
                    return {
                        "service": service_name,
                        "status": "unhealthy",
                        "response_time": response_time,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            response_time = time.time() - start_time
            service.update_health(False, response_time)
            
            return {
                "service": service_name,
                "status": "unhealthy",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def check_all_services_health(self) -> Dict[str, Any]:
        """Проверить здоровье всех сервисов"""
        results = {}
        
        for service_name in self.services:
            results[service_name] = await self.check_service_health(service_name)
        
        return results
    
    def get_service_info(self, service_name: str) -> Optional[ServiceEndpoint]:
        """Получить информацию о сервисе"""
        return self.services.get(service_name)
    
    def get_all_services_info(self) -> Dict[str, ServiceEndpoint]:
        """Получить информацию о всех сервисах"""
        return self.services.copy()
    
    async def close(self):
        """Закрыть сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
