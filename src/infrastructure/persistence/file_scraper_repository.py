"""
Файловая реализация репозитория скрапера
"""
import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from src.domain.repositories.scraper_repository import ScraperRepository
from src.domain.entities.scraped_data import ScrapedData, ScrapingJob

class FileScraperRepository(ScraperRepository):
    """Файловая реализация репозитория скрапера"""
    
    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = Path(data_dir)
        self.jobs_file = self.data_dir / "jobs.json"
        self.data_file = self.data_dir / "scraped_data.json"
        
        # Создаем директорию если не существует
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Инициализируем файлы если не существуют
        if not self.jobs_file.exists():
            self._save_jobs({})
        
        if not self.data_file.exists():
            self._save_data({})
    
    def _load_jobs(self) -> Dict[str, ScrapingJob]:
        """Загрузка задач из файла"""
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
                result = {}
                for job_id, job_data in jobs_data.items():
                    # Преобразуем строки дат обратно в datetime объекты
                    if job_data.get('created_at'):
                        job_data['created_at'] = datetime.fromisoformat(job_data['created_at'])
                    if job_data.get('started_at'):
                        job_data['started_at'] = datetime.fromisoformat(job_data['started_at'])
                    if job_data.get('completed_at'):
                        job_data['completed_at'] = datetime.fromisoformat(job_data['completed_at'])
                    
                    result[job_id] = ScrapingJob(**job_data)
                return result
        except Exception as e:
            print(f"Ошибка загрузки задач: {e}")
            return {}
    
    def _save_jobs(self, jobs: Dict[str, ScrapingJob]) -> None:
        """Сохранение задач в файл"""
        try:
            jobs_data = {
                job_id: {
                    "job_id": job.job_id,
                    "status": job.status,
                    "source": job.source,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "error": job.error,
                    "progress": job.progress,
                    "items_processed": job.items_processed,
                    "items_total": job.items_total
                }
                for job_id, job in jobs.items()
            }
            
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения задач: {e}")
    
    def _load_data(self) -> Dict[str, ScrapedData]:
        """Загрузка данных из файла"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)
                result = {}
                for data_id, data_item in data_dict.items():
                    # Преобразуем строки дат обратно в datetime объекты
                    if data_item.get('date'):
                        data_item['date'] = datetime.fromisoformat(data_item['date'])
                    if data_item.get('created_at'):
                        data_item['created_at'] = datetime.fromisoformat(data_item['created_at'])
                    
                    result[data_id] = ScrapedData(**data_item)
                return result
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            return {}
    
    def _save_data(self, data: Dict[str, ScrapedData]) -> None:
        """Сохранение данных в файл"""
        try:
            data_dict = {
                data_id: {
                    "id": item.id,
                    "number": item.number,
                    "date": item.date.isoformat() if item.date else None,
                    "content": item.content,
                    "source": item.source,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                }
                for data_id, item in data.items()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")
    
    def save_job(self, job: ScrapingJob) -> str:
        """Сохранение задачи парсинга"""
        jobs = self._load_jobs()
        jobs[job.job_id] = job
        self._save_jobs(jobs)
        return job.job_id
    
    def get_job(self, job_id: str) -> Optional[ScrapingJob]:
        """Получение задачи по ID"""
        jobs = self._load_jobs()
        return jobs.get(job_id)
    
    def get_all_jobs(self) -> List[ScrapingJob]:
        """Получение всех задач"""
        jobs = self._load_jobs()
        return list(jobs.values())
    
    def update_job_status(self, job_id: str, status: str, error: Optional[str] = None, progress: float = 0.0, items_processed: int = 0, items_total: int = 0) -> bool:
        """Обновление статуса задачи"""
        jobs = self._load_jobs()
        if job_id in jobs:
            job = jobs[job_id]
            job.status = status
            job.progress = progress
            job.items_processed = items_processed
            job.items_total = items_total
            
            if status == "running" and not job.started_at:
                job.started_at = datetime.now()
            elif status in ["completed", "failed"] and not job.completed_at:
                job.completed_at = datetime.now()
            
            if error:
                job.error = error
            
            self._save_jobs(jobs)
            return True
        return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Отмена задачи"""
        jobs = self._load_jobs()
        if job_id in jobs:
            jobs[job_id].status = "cancelled"
            jobs[job_id].completed_at = datetime.now()
            self._save_jobs(jobs)
            return True
        return False
    
    def save_data(self, data: ScrapedData) -> str:
        """Сохранение данных"""
        all_data = self._load_data()
        all_data[data.id] = data
        self._save_data(all_data)
        return data.id
    
    def get_latest_data(self, limit: int = 10) -> List[ScrapedData]:
        """Получение последних данных"""
        all_data = self._load_data()
        sorted_data = sorted(
            all_data.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return sorted_data[:limit]
    
    def get_all_data(self) -> List[ScrapedData]:
        """Получение всех данных"""
        all_data = self._load_data()
        return list(all_data.values())
    
    def get_data_count(self) -> int:
        """Получение количества данных"""
        all_data = self._load_data()
        return len(all_data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        jobs = self._load_jobs()
        all_data = self._load_data()
        
        total_jobs = len(jobs)
        completed_jobs = len([
            job for job in jobs.values()
            if job.status == "completed"
        ])
        failed_jobs = len([
            job for job in jobs.values()
            if job.status == "failed"
        ])
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "total_data": len(all_data),
            "success_rate": completed_jobs / total_jobs if total_jobs > 0 else 0
        } 