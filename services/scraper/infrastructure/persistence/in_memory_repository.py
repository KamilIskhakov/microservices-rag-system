"""
In-Memory реализация репозитория для Scraper Service
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from domain.repositories.scraper_repository import ScraperRepository
from domain.entities.scraped_data import ScrapedData, ScrapingJob

logger = logging.getLogger(__name__)


class InMemoryScraperRepository(ScraperRepository):
    """In-Memory реализация репозитория скрапера"""
    
    def __init__(self):
        self.scraped_data: Dict[str, ScrapedData] = {}
        self.scraping_jobs: Dict[str, ScrapingJob] = {}
        self._data_count = 0
        self._job_count = 0
    
    def save_scraped_data(self, data: ScrapedData) -> str:
        """Сохранить скрапленные данные"""
        data_id = str(data.id)
        self.scraped_data[data_id] = data
        
        self._data_count += 1
        logger.info(f"Скрапленные данные сохранены: {data_id}")
        return data_id
    
    def get_scraped_data(self, data_id: str) -> Optional[ScrapedData]:
        """Получить скрапленные данные по ID"""
        return self.scraped_data.get(data_id)
    
    def update_scraped_data_status(self, data_id: str, status: str) -> bool:
        """Обновить статус скрапленных данных"""
        if data_id in self.scraped_data:
            self.scraped_data[data_id].status = status
            self.scraped_data[data_id].updated_at = datetime.now()
            logger.info(f"Статус данных {data_id} обновлен: {status}")
            return True
        return False
    
    def get_all_scraped_data(self, limit: int = 100) -> List[ScrapedData]:
        """Получить все скрапленные данные"""
        all_data = list(self.scraped_data.values())
        return all_data[-limit:] if len(all_data) > limit else all_data
    
    def save_scraping_job(self, job: ScrapingJob) -> str:
        """Сохранить задачу скрапинга"""
        job_id = str(job.id)
        self.scraping_jobs[job_id] = job
        
        self._job_count += 1
        logger.info(f"Задача скрапинга сохранена: {job_id}")
        return job_id
    
    def get_scraping_job(self, job_id: str) -> Optional[ScrapingJob]:
        """Получить задачу скрапинга по ID"""
        return self.scraping_jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: str) -> bool:
        """Обновить статус задачи"""
        if job_id in self.scraping_jobs:
            self.scraping_jobs[job_id].status = status
            self.scraping_jobs[job_id].updated_at = datetime.now()
            logger.info(f"Статус задачи {job_id} обновлен: {status}")
            return True
        return False
    
    def get_pending_jobs(self) -> List[ScrapingJob]:
        """Получить ожидающие задачи"""
        return [job for job in self.scraping_jobs.values() if job.status == "pending"]
    
    def get_running_jobs(self) -> List[ScrapingJob]:
        """Получить выполняющиеся задачи"""
        return [job for job in self.scraping_jobs.values() if job.status == "running"]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        total_data = len(self.scraped_data)
        processed_data = len([d for d in self.scraped_data.values() if d.status == "processed"])
        failed_data = len([d for d in self.scraped_data.values() if d.status == "failed"])
        pending_data = len([d for d in self.scraped_data.values() if d.status == "pending"])
        
        total_jobs = len(self.scraping_jobs)
        completed_jobs = len([j for j in self.scraping_jobs.values() if j.status == "completed"])
        failed_jobs = len([j for j in self.scraping_jobs.values() if j.status == "failed"])
        pending_jobs = len([j for j in self.scraping_jobs.values() if j.status == "pending"])
        running_jobs = len([j for j in self.scraping_jobs.values() if j.status == "running"])
        
        return {
            "total_scraped_data": total_data,
            "processed_data": processed_data,
            "failed_data": failed_data,
            "pending_data": pending_data,
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "pending_jobs": pending_jobs,
            "running_jobs": running_jobs
        }
    
    def delete_scraped_data(self, data_id: str) -> bool:
        """Удалить скрапленные данные"""
        if data_id in self.scraped_data:
            del self.scraped_data[data_id]
            logger.info(f"Скрапленные данные удалены: {data_id}")
            return True
        return False
    
    def delete_scraping_job(self, job_id: str) -> bool:
        """Удалить задачу скрапинга"""
        if job_id in self.scraping_jobs:
            del self.scraping_jobs[job_id]
            logger.info(f"Задача скрапинга удалена: {job_id}")
            return True
        return False
