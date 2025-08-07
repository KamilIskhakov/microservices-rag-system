"""
Репозиторий для работы со скрапленными данными в Scraper Service
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.scraped_data import ScrapedData, ScrapingJob


class ScraperRepository(ABC):
    """Абстрактный репозиторий для работы со скрапленными данными"""
    
    @abstractmethod
    def save_scraped_data(self, data: ScrapedData) -> str:
        """Сохранить скрапленные данные"""
        pass
    
    @abstractmethod
    def get_scraped_data(self, data_id: str) -> Optional[ScrapedData]:
        """Получить скрапленные данные по ID"""
        pass
    
    @abstractmethod
    def update_scraped_data_status(self, data_id: str, status: str) -> bool:
        """Обновить статус скрапленных данных"""
        pass
    
    @abstractmethod
    def get_all_scraped_data(self, limit: int = 100) -> List[ScrapedData]:
        """Получить все скрапленные данные"""
        pass
    
    @abstractmethod
    def save_scraping_job(self, job: ScrapingJob) -> str:
        """Сохранить задачу скрапинга"""
        pass
    
    @abstractmethod
    def get_scraping_job(self, job_id: str) -> Optional[ScrapingJob]:
        """Получить задачу скрапинга по ID"""
        pass
    
    @abstractmethod
    def update_job_status(self, job_id: str, status: str) -> bool:
        """Обновить статус задачи"""
        pass
    
    @abstractmethod
    def get_pending_jobs(self) -> List[ScrapingJob]:
        """Получить ожидающие задачи"""
        pass
    
    @abstractmethod
    def get_running_jobs(self) -> List[ScrapingJob]:
        """Получить выполняющиеся задачи"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику"""
        pass
    
    @abstractmethod
    def delete_scraped_data(self, data_id: str) -> bool:
        """Удалить скрапленные данные"""
        pass
    
    @abstractmethod
    def delete_scraping_job(self, job_id: str) -> bool:
        """Удалить задачу скрапинга"""
        pass
