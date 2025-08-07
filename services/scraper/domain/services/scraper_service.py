"""
Доменный сервис для работы со скрапингом в Scraper Service
"""
import logging
import asyncio
import aiohttp
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from ..entities.scraped_data import ScrapedData, ScrapingJob
from ..repositories.scraper_repository import ScraperRepository

logger = logging.getLogger(__name__)


class ScraperService:
    """Доменный сервис для работы со скрапингом"""
    
    def __init__(self, scraper_repository: ScraperRepository):
        self.scraper_repository = scraper_repository
        self.vectorstore_url = "http://vectorstore:8002"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить HTTP сессию"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def create_scraping_job(self, source_url: str, job_type: str = "minjust") -> ScrapingJob:
        """Создать задачу скрапинга"""
        job = ScrapingJob(
            id=None,
            source_url=source_url,
            job_type=job_type
        )
        
        job_id = self.scraper_repository.save_scraping_job(job)
        logger.info(f"Создана задача скрапинга: {job_id} для {source_url}")
        
        return job
    
    async def execute_scraping_job(self, job_id: str) -> Dict[str, Any]:
        """Выполнить задачу скрапинга"""
        job = self.scraper_repository.get_scraping_job(job_id)
        if not job:
            raise ValueError(f"Задача {job_id} не найдена")
        
        try:
            # Начинаем выполнение
            job.start()
            self.scraper_repository.update_job_status(job_id, "running")
            
            logger.info(f"Выполняем задачу скрапинга: {job_id}")
            
            # Выполняем скрапинг в зависимости от типа
            if job.job_type == "minjust":
                scraped_data = await self._scrape_minjust(job.source_url)
            else:
                scraped_data = await self._scrape_generic(job.source_url)
            
            # Сохраняем скрапленные данные
            data_id = self.scraper_repository.save_scraped_data(scraped_data)
            
            # Отправляем в Vector Store
            await self._send_to_vectorstore(scraped_data)
            
            # Завершаем задачу
            job.complete()
            self.scraper_repository.update_job_status(job_id, "completed")
            
            logger.info(f"Задача {job_id} выполнена успешно")
            
            return {
                "success": True,
                "job_id": job_id,
                "data_id": data_id,
                "status": "completed"
            }
            
        except Exception as e:
            job.fail(str(e))
            self.scraper_repository.update_job_status(job_id, "failed")
            logger.error(f"Ошибка выполнения задачи {job_id}: {e}")
            
            return {
                "success": False,
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _scrape_minjust(self, url: str) -> ScrapedData:
        """Скрапить данные с сайта Минюста"""
        session = await self._get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                content = await response.text()
                
                # Извлекаем заголовок
                title = self._extract_title(content)
                
                # Создаем объект данных
                scraped_data = ScrapedData(
                    id=None,
                    source_url=url,
                    content=content,
                    title=title,
                    metadata={
                        "scraper_type": "minjust",
                        "content_length": len(content),
                        "scraped_at": datetime.now().isoformat()
                    }
                )
                
                return scraped_data
                
        except Exception as e:
            logger.error(f"Ошибка скрапинга {url}: {e}")
            raise
    
    async def _scrape_generic(self, url: str) -> ScrapedData:
        """Скрапить данные с любого сайта"""
        session = await self._get_session()
        
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                content = await response.text()
                
                # Извлекаем заголовок
                title = self._extract_title(content)
                
                # Создаем объект данных
                scraped_data = ScrapedData(
                    id=None,
                    source_url=url,
                    content=content,
                    title=title,
                    metadata={
                        "scraper_type": "generic",
                        "content_length": len(content),
                        "scraped_at": datetime.now().isoformat()
                    }
                )
                
                return scraped_data
                
        except Exception as e:
            logger.error(f"Ошибка скрапинга {url}: {e}")
            raise
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Извлечь заголовок из HTML"""
        try:
            import re
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                return title_match.group(1).strip()
        except Exception:
            pass
        return None
    
    async def _send_to_vectorstore(self, scraped_data: ScrapedData) -> None:
        """Отправить данные в Vector Store"""
        try:
            session = await self._get_session()
            
            # Подготавливаем данные для отправки
            document_data = {
                "content": scraped_data.content,
                "metadata": {
                    "source_url": scraped_data.source_url,
                    "title": scraped_data.title,
                    "scraper_type": scraped_data.metadata.get("scraper_type"),
                    "scraped_at": scraped_data.metadata.get("scraped_at")
                }
            }
            
            async with session.post(
                f"{self.vectorstore_url}/add-document",
                json=document_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Данные отправлены в Vector Store: {result.get('document_id')}")
                else:
                    logger.warning(f"Ошибка отправки в Vector Store: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка отправки в Vector Store: {e}")
    
    def get_scraped_data(self, data_id: str) -> Optional[ScrapedData]:
        """Получить скрапленные данные по ID"""
        return self.scraper_repository.get_scraped_data(data_id)
    
    def get_scraping_job(self, job_id: str) -> Optional[ScrapingJob]:
        """Получить задачу скрапинга по ID"""
        return self.scraper_repository.get_scraping_job(job_id)
    
    def get_pending_jobs(self) -> List[ScrapingJob]:
        """Получить ожидающие задачи"""
        return self.scraper_repository.get_pending_jobs()
    
    def get_running_jobs(self) -> List[ScrapingJob]:
        """Получить выполняющиеся задачи"""
        return self.scraper_repository.get_running_jobs()
    
    def get_all_scraped_data(self, limit: int = 100) -> List[ScrapedData]:
        """Получить все скрапленные данные"""
        return self.scraper_repository.get_all_scraped_data(limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        return self.scraper_repository.get_statistics()
    
    def delete_scraped_data(self, data_id: str) -> bool:
        """Удалить скрапленные данные"""
        return self.scraper_repository.delete_scraped_data(data_id)
    
    def delete_scraping_job(self, job_id: str) -> bool:
        """Удалить задачу скрапинга"""
        return self.scraper_repository.delete_scraping_job(job_id)
    
    async def close(self):
        """Закрыть сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
