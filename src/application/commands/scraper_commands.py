"""
Команды для работы со скрапером
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from src.domain.repositories.scraper_repository import ScraperRepository
from src.domain.entities.scraped_data import ScrapedData, ScrapingJob
from src.application.commands.command_bus import CommandBus

@dataclass
class StartScrapingCommand:
    """Команда запуска парсинга"""
    source: str = "minjust"
    force_update: bool = False
    max_items: Optional[int] = None

@dataclass
class StartScrapingResult:
    """Результат запуска парсинга"""
    job_id: str
    status: str = "pending"

@dataclass
class GetScrapingStatusCommand:
    """Команда получения статуса парсинга"""
    job_id: str

@dataclass
class GetScrapingStatusResult:
    """Результат получения статуса парсинга"""
    job_id: str
    status: str
    progress: float = 0.0
    items_processed: int = 0
    items_total: int = 0
    start_time: str = ""
    end_time: Optional[str] = None
    error: Optional[str] = None

class StartScrapingCommandHandler:
    """Обработчик команды запуска парсинга"""
    
    def __init__(self, scraper_repository: ScraperRepository):
        self.scraper_repository = scraper_repository
    
    async def handle(self, command: StartScrapingCommand) -> StartScrapingResult:
        """Обработка команды запуска парсинга"""
        # Создаем задачу парсинга
        job = ScrapingJob(
            job_id=None,  # Будет сгенерирован автоматически
            source=command.source,
            status="pending"
        )
        
        # Сохраняем задачу
        job_id = self.scraper_repository.save_job(job)
        
        return StartScrapingResult(
            job_id=job_id,
            status="pending"
        )

class GetScrapingStatusCommandHandler:
    """Обработчик команды получения статуса парсинга"""
    
    def __init__(self, scraper_repository: ScraperRepository):
        self.scraper_repository = scraper_repository
    
    async def handle(self, command: GetScrapingStatusCommand) -> GetScrapingStatusResult:
        """Обработка команды получения статуса парсинга"""
        # Получаем задачу
        job = self.scraper_repository.get_job(command.job_id)
        
        if not job:
            raise ValueError(f"Job {command.job_id} not found")
        
        return GetScrapingStatusResult(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            items_processed=job.items_processed,
            items_total=job.items_total,
            start_time=job.created_at.isoformat(),
            end_time=job.completed_at.isoformat() if job.completed_at else None,
            error=job.error
        ) 