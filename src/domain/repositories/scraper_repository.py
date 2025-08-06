"""
Репозиторий для скрапера
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.domain.entities.scraped_data import ScrapedData, ScrapingJob

class ScraperRepository(ABC):
    """Абстрактный репозиторий для скрапера"""
    
    @abstractmethod
    def save_job(self, job: ScrapingJob) -> str:
        """Сохранение задачи парсинга"""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[ScrapingJob]:
        """Получение задачи по ID"""
        pass
    
    @abstractmethod
    def get_all_jobs(self) -> List[ScrapingJob]:
        """Получение всех задач"""
        pass
    
    @abstractmethod
    def update_job_status(self, job_id: str, status: str, error: Optional[str] = None) -> bool:
        """Обновление статуса задачи"""
        pass
    
    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Отмена задачи"""
        pass
    
    @abstractmethod
    def save_data(self, data: ScrapedData) -> str:
        """Сохранение данных"""
        pass
    
    @abstractmethod
    def get_latest_data(self, limit: int = 10) -> List[ScrapedData]:
        """Получение последних данных"""
        pass
    
    @abstractmethod
    def get_all_data(self) -> List[ScrapedData]:
        """Получение всех данных"""
        pass
    
    @abstractmethod
    def get_data_count(self) -> int:
        """Получение количества данных"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        pass

class InMemoryScraperRepository(ScraperRepository):
    """In-memory реализация репозитория скрапера"""
    
    def __init__(self):
        self.jobs: Dict[str, ScrapingJob] = {}
        self.data: Dict[str, ScrapedData] = {}
    
    def save_job(self, job: ScrapingJob) -> str:
        """Сохранение задачи парсинга"""
        self.jobs[job.job_id] = job
        return job.job_id
    
    def get_job(self, job_id: str) -> Optional[ScrapingJob]:
        """Получение задачи по ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[ScrapingJob]:
        """Получение всех задач"""
        return list(self.jobs.values())
    
    def update_job_status(self, job_id: str, status: str, error: Optional[str] = None) -> bool:
        """Обновление статуса задачи"""
        if job_id in self.jobs:
            self.jobs[job_id].status = status
            if status == "running" and not self.jobs[job_id].started_at:
                self.jobs[job_id].started_at = datetime.now()
            elif status in ["completed", "failed"] and not self.jobs[job_id].completed_at:
                self.jobs[job_id].completed_at = datetime.now()
            if error:
                self.jobs[job_id].error = error
            return True
        return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Отмена задачи"""
        if job_id in self.jobs:
            self.jobs[job_id].status = "cancelled"
            self.jobs[job_id].completed_at = datetime.now()
            return True
        return False
    
    def save_data(self, data: ScrapedData) -> str:
        """Сохранение данных"""
        self.data[data.id] = data
        return data.id
    
    def get_latest_data(self, limit: int = 10) -> List[ScrapedData]:
        """Получение последних данных"""
        sorted_data = sorted(
            self.data.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return sorted_data[:limit]
    
    def get_data_count(self) -> int:
        """Получение количества данных"""
        return len(self.data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        total_jobs = len(self.jobs)
        completed_jobs = len([
            job for job in self.jobs.values()
            if job.status == "completed"
        ])
        failed_jobs = len([
            job for job in self.jobs.values()
            if job.status == "failed"
        ])
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "total_data": len(self.data),
            "success_rate": completed_jobs / total_jobs if total_jobs > 0 else 0
        } 