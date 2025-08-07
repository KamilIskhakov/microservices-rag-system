#!/usr/bin/env python3
"""
Скрипт для нагрузочного тестирования Vector Store
Тестирует 2000 запросов одновременно
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация теста
VECTORSTORE_URL = "http://localhost:8002"
REQUEST_PROCESSOR_URL = "http://localhost:8004"
TOTAL_REQUESTS = 2000
CONCURRENT_REQUESTS = 100  # Максимум одновременных запросов
QUERIES = [
    "музыка",
    "книга",
    "видео",
    "статья",
    "документ",
    "решение суда",
    "запрещенный контент",
    "интернет",
    "социальная сеть",
    "публикация"
]

class LoadTester:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    
    async def make_request(self, session: aiohttp.ClientSession, query: str, request_id: int) -> Dict[str, Any]:
        """Выполняет один запрос к Vector Store"""
        async with self.semaphore:
            start_time = time.time()
            
            try:
                # Тестируем прямой запрос к Vector Store
                payload = {
                    "query": query,
                    "top_k": 5,
                    "threshold": 0.5
                }
                
                async with session.post(
                    f"{VECTORSTORE_URL}/search",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    end_time = time.time()
                    processing_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "request_id": request_id,
                            "query": query,
                            "status": "success",
                            "processing_time": processing_time,
                            "response_time": data.get("processing_time", 0),
                            "total_results": data.get("total_results", 0),
                            "http_status": response.status
                        }
                    else:
                        return {
                            "request_id": request_id,
                            "query": query,
                            "status": "error",
                            "processing_time": processing_time,
                            "error": f"HTTP {response.status}",
                            "http_status": response.status
                        }
                        
            except Exception as e:
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "query": query,
                    "status": "error",
                    "processing_time": end_time - start_time,
                    "error": str(e),
                    "http_status": 0
                }
    
    async def test_vectorstore_direct(self):
        """Тестирует прямые запросы к Vector Store"""
        logger.info(f"🚀 Начинаем нагрузочное тестирование Vector Store")
        logger.info(f"📊 Всего запросов: {TOTAL_REQUESTS}")
        logger.info(f"⚡ Одновременных запросов: {CONCURRENT_REQUESTS}")
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for i in range(TOTAL_REQUESTS):
                query = QUERIES[i % len(QUERIES)]
                task = self.make_request(session, query, i)
                tasks.append(task)
            
            # Выполняем все запросы одновременно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Фильтруем исключения
            self.results = [r for r in results if isinstance(r, dict)]
        
        total_time = time.time() - start_time
        
        # Анализируем результаты
        self.analyze_results(total_time)
    
    async def test_request_processor(self):
        """Тестирует запросы через Request Processor"""
        logger.info(f"🚀 Начинаем нагрузочное тестирование Request Processor")
        logger.info(f"📊 Всего запросов: {TOTAL_REQUESTS}")
        logger.info(f"⚡ Одновременных запросов: {CONCURRENT_REQUESTS}")
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for i in range(TOTAL_REQUESTS):
                query = QUERIES[i % len(QUERIES)]
                task = self.make_request_processor(session, query, i)
                tasks.append(task)
            
            # Выполняем все запросы одновременно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Фильтруем исключения
            self.results = [r for r in results if isinstance(r, dict)]
        
        total_time = time.time() - start_time
        
        # Анализируем результаты
        self.analyze_results(total_time)
    
    async def make_request_processor(self, session: aiohttp.ClientSession, query: str, request_id: int) -> Dict[str, Any]:
        """Выполняет запрос через Request Processor"""
        async with self.semaphore:
            start_time = time.time()
            
            try:
                payload = {
                    "query": query,
                    "user_id": f"load_test_user_{request_id}",
                    "services": ["vectorstore"]
                }
                
                async with session.post(
                    f"{REQUEST_PROCESSOR_URL}/process",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    end_time = time.time()
                    processing_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        vectorstore_result = data.get("results", {}).get("vectorstore", {})
                        return {
                            "request_id": request_id,
                            "query": query,
                            "status": "success",
                            "processing_time": processing_time,
                            "response_time": data.get("processing_time", 0),
                            "vectorstore_time": vectorstore_result.get("processing_time", 0),
                            "total_results": vectorstore_result.get("total_results", 0),
                            "http_status": response.status
                        }
                    else:
                        return {
                            "request_id": request_id,
                            "query": query,
                            "status": "error",
                            "processing_time": processing_time,
                            "error": f"HTTP {response.status}",
                            "http_status": response.status
                        }
                        
            except Exception as e:
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "query": query,
                    "status": "error",
                    "processing_time": end_time - start_time,
                    "error": str(e),
                    "http_status": 0
                }
    
    def analyze_results(self, total_time: float):
        """Анализирует результаты тестирования"""
        successful_requests = [r for r in self.results if r["status"] == "success"]
        failed_requests = [r for r in self.results if r["status"] == "error"]
        
        if not successful_requests:
            logger.error("❌ Нет успешных запросов!")
            return
        
        # Временные метрики
        processing_times = [r["processing_time"] for r in successful_requests]
        response_times = [r.get("response_time", 0) for r in successful_requests]
        
        # Статистика
        total_requests = len(self.results)
        success_rate = len(successful_requests) / total_requests * 100
        requests_per_second = total_requests / total_time
        
        logger.info("=" * 60)
        logger.info("📊 РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
        logger.info("=" * 60)
        logger.info(f"🕐 Общее время: {total_time:.2f} секунд")
        logger.info(f"📈 Всего запросов: {total_requests}")
        logger.info(f"✅ Успешных запросов: {len(successful_requests)}")
        logger.info(f"❌ Неудачных запросов: {len(failed_requests)}")
        logger.info(f"📊 Успешность: {success_rate:.1f}%")
        logger.info(f"⚡ Запросов в секунду: {requests_per_second:.1f}")
        
        logger.info("\n📈 ВРЕМЕННЫЕ МЕТРИКИ (общее время запроса):")
        logger.info(f"   Среднее: {statistics.mean(processing_times):.3f} сек")
        logger.info(f"   Медиана: {statistics.median(processing_times):.3f} сек")
        logger.info(f"   Минимум: {min(processing_times):.3f} сек")
        logger.info(f"   Максимум: {max(processing_times):.3f} сек")
        logger.info(f"   Стандартное отклонение: {statistics.stdev(processing_times):.3f} сек")
        
        if any(response_times):
            logger.info("\n📈 ВРЕМЕННЫЕ МЕТРИКИ (время обработки сервиса):")
            response_times_filtered = [t for t in response_times if t > 0]
            if response_times_filtered:
                logger.info(f"   Среднее: {statistics.mean(response_times_filtered):.3f} сек")
                logger.info(f"   Медиана: {statistics.median(response_times_filtered):.3f} сек")
                logger.info(f"   Минимум: {min(response_times_filtered):.3f} сек")
                logger.info(f"   Максимум: {max(response_times_filtered):.3f} сек")
        
        # Результаты поиска
        total_results = sum(r.get("total_results", 0) for r in successful_requests)
        avg_results = total_results / len(successful_requests) if successful_requests else 0
        logger.info(f"\n🔍 РЕЗУЛЬТАТЫ ПОИСКА:")
        logger.info(f"   Всего найденных документов: {total_results}")
        logger.info(f"   Среднее документов на запрос: {avg_results:.1f}")
        
        # Ошибки
        if failed_requests:
            logger.info(f"\n❌ ОШИБКИ:")
            error_types = {}
            for req in failed_requests:
                error = req.get("error", "Unknown")
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                logger.info(f"   {error}: {count} раз")
        
        logger.info("=" * 60)

async def main():
    """Основная функция"""
    tester = LoadTester()
    
    print("Выберите тип тестирования:")
    print("1. Прямые запросы к Vector Store")
    print("2. Запросы через Request Processor")
    
    choice = input("Введите номер (1 или 2): ").strip()
    
    if choice == "1":
        await tester.test_vectorstore_direct()
    elif choice == "2":
        await tester.test_request_processor()
    else:
        print("Неверный выбор!")

if __name__ == "__main__":
    asyncio.run(main())
