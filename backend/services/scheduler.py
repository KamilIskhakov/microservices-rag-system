import asyncio
import logging
from datetime import datetime, time
from typing import Optional, Callable
from dataclasses import dataclass

from services.logger import logger
from services.database_updater import DatabaseUpdater, UpdateResult


@dataclass
class ScheduledTask:
    """Модель запланированной задачи"""
    name: str
    func: Callable
    interval_hours: int
    last_run: Optional[datetime] = None
    is_running: bool = False
    error_count: int = 0
    max_errors: int = 3


class TaskScheduler:
    """Планировщик задач для автоматического обновления"""
    
    def __init__(self):
        self.tasks: dict[str, ScheduledTask] = {}
        self.is_running = False
        self.update_task: Optional[ScheduledTask] = None
        
    def add_database_update_task(self, updater: DatabaseUpdater, interval_hours: int = 24):
        """Добавляет задачу обновления базы данных"""
        self.update_task = ScheduledTask(
            name="database_update",
            func=updater.update_database,
            interval_hours=interval_hours
        )
        self.tasks["database_update"] = self.update_task
        logger.info(f"Добавлена задача обновления БД с интервалом {interval_hours} часов")
    
    async def start(self):
        """Запускает планировщик задач"""
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return
            
        self.is_running = True
        logger.info("Планировщик задач запущен")
        
        try:
            while self.is_running:
                await self._run_pending_tasks()
                await asyncio.sleep(60)  # Проверяем каждую минуту
                
        except Exception as e:
            logger.error(f"Ошибка в планировщике задач: {e}")
        finally:
            self.is_running = False
            logger.info("Планировщик задач остановлен")
    
    async def stop(self):
        """Останавливает планировщик задач"""
        self.is_running = False
        logger.info("Остановка планировщика задач...")
    
    async def run_task_now(self, task_name: str) -> Optional[UpdateResult]:
        """Запускает задачу немедленно"""
        if task_name not in self.tasks:
            logger.error(f"Задача {task_name} не найдена")
            return None
            
        task = self.tasks[task_name]
        if task.is_running:
            logger.warning(f"Задача {task_name} уже выполняется")
            return None
            
        try:
            task.is_running = True
            task.last_run = datetime.now()
            
            logger.info(f"Запуск задачи {task_name}...")
            result = await task.func()
            
            if result and hasattr(result, 'success') and result.success:
                task.error_count = 0
                logger.info(f"Задача {task_name} выполнена успешно")
            else:
                task.error_count += 1
                logger.error(f"Задача {task_name} завершилась с ошибкой")
            
            return result
            
        except Exception as e:
            task.error_count += 1
            logger.error(f"Ошибка выполнения задачи {task_name}: {e}")
            return None
        finally:
            task.is_running = False
    
    async def get_task_status(self, task_name: str) -> dict:
        """Получает статус задачи"""
        if task_name not in self.tasks:
            return {"error": f"Задача {task_name} не найдена"}
            
        task = self.tasks[task_name]
        return {
            "name": task.name,
            "is_running": task.is_running,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "error_count": task.error_count,
            "interval_hours": task.interval_hours
        }
    
    async def _run_pending_tasks(self):
        """Выполняет задачи, которые должны быть запущены"""
        current_time = datetime.now()
        
        for task_name, task in self.tasks.items():
            if task.is_running:
                continue
                
            if task.error_count >= task.max_errors:
                logger.warning(f"Задача {task_name} пропущена из-за превышения лимита ошибок")
                continue
            
            should_run = self._should_run_task(task, current_time)
            if should_run:
                asyncio.create_task(self.run_task_now(task_name))
    
    def _should_run_task(self, task: ScheduledTask, current_time: datetime) -> bool:
        """Проверяет, должна ли задача быть запущена"""
        if task.last_run is None:
            return True
            
        time_since_last_run = current_time - task.last_run
        return time_since_last_run.total_seconds() >= task.interval_hours * 3600 