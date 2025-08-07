"""
Стратегии многопоточности для AI Model Service
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import os

logger = logging.getLogger(__name__)


class ThreadingStrategy(ABC):
    """Абстрактная стратегия многопоточности"""
    
    @abstractmethod
    def execute_task(self, task: Callable, *args, **kwargs) -> Any:
        """Выполнить задачу"""
        pass
    
    @abstractmethod
    def execute_tasks_concurrently(self, tasks: List[Callable], *args, **kwargs) -> List[Any]:
        """Выполнить задачи параллельно"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Очистка ресурсов"""
        pass


class AsyncThreadingStrategy(ThreadingStrategy):
    """Асинхронная стратегия с ThreadPoolExecutor"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        logger.info(f"Инициализирован AsyncThreadingStrategy с {self.max_workers} рабочими потоками")
    
    async def execute_task(self, task: Callable, *args, **kwargs) -> Any:
        """Выполнить задачу асинхронно"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, task, *args, **kwargs)
    
    async def execute_tasks_concurrently(self, tasks: List[Callable], *args, **kwargs) -> List[Any]:
        """Выполнить задачи параллельно"""
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(self.executor, task, *args, **kwargs)
            for task in tasks
        ]
        return await asyncio.gather(*futures, return_exceptions=True)
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("ThreadPoolExecutor завершен")


class ProcessThreadingStrategy(ThreadingStrategy):
    """Стратегия с ProcessPoolExecutor для CPU-интенсивных задач"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(4, os.cpu_count() or 1)
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        logger.info(f"Инициализирован ProcessThreadingStrategy с {self.max_workers} процессами")
    
    async def execute_task(self, task: Callable, *args, **kwargs) -> Any:
        """Выполнить задачу в отдельном процессе"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, task, *args, **kwargs)
    
    async def execute_tasks_concurrently(self, tasks: List[Callable], *args, **kwargs) -> List[Any]:
        """Выполнить задачи параллельно в процессах"""
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(self.executor, task, *args, **kwargs)
            for task in tasks
        ]
        return await asyncio.gather(*futures, return_exceptions=True)
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("ProcessPoolExecutor завершен")


class HybridThreadingStrategy(ThreadingStrategy):
    """Гибридная стратегия с выбором между потоками и процессами"""
    
    def __init__(self, thread_workers: int = None, process_workers: int = None):
        self.thread_workers = thread_workers or min(32, (os.cpu_count() or 1) + 4)
        self.process_workers = process_workers or min(4, os.cpu_count() or 1)
        
        self.thread_executor = ThreadPoolExecutor(max_workers=self.thread_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=self.process_workers)
        
        logger.info(f"Инициализирован HybridThreadingStrategy: {self.thread_workers} потоков, {self.process_workers} процессов")
    
    async def execute_task(self, task: Callable, *args, **kwargs) -> Any:
        """Выполнить задачу с автоматическим выбором исполнителя"""
        # Определяем тип задачи по имени или аннотациям
        executor = self._select_executor(task)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, task, *args, **kwargs)
    
    async def execute_tasks_concurrently(self, tasks: List[Callable], *args, **kwargs) -> List[Any]:
        """Выполнить задачи параллельно с оптимальным распределением"""
        loop = asyncio.get_event_loop()
        futures = []
        
        for task in tasks:
            executor = self._select_executor(task)
            future = loop.run_in_executor(executor, task, *args, **kwargs)
            futures.append(future)
        
        return await asyncio.gather(*futures, return_exceptions=True)
    
    def _select_executor(self, task: Callable) -> ThreadPoolExecutor | ProcessPoolExecutor:
        """Выбрать подходящий исполнитель для задачи"""
        task_name = task.__name__.lower()
        
        # CPU-интенсивные задачи
        cpu_intensive_keywords = ['compute', 'calculate', 'process', 'generate', 'encode']
        if any(keyword in task_name for keyword in cpu_intensive_keywords):
            return self.process_executor
        
        # I/O-интенсивные задачи
        return self.thread_executor
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)
        if self.process_executor:
            self.process_executor.shutdown(wait=True)
        logger.info("HybridThreadingStrategy завершен")


class ThreadingStrategyFactory:
    """Фабрика для создания стратегий многопоточности"""
    
    _strategies = {
        "async": AsyncThreadingStrategy,
        "process": ProcessThreadingStrategy,
        "hybrid": HybridThreadingStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_type: str = "hybrid", **kwargs) -> ThreadingStrategy:
        """Создать стратегию по типу"""
        strategy_class = cls._strategies.get(strategy_type)
        if not strategy_class:
            logger.warning(f"Неизвестная стратегия {strategy_type}, используем hybrid")
            strategy_class = HybridThreadingStrategy
        
        return strategy_class(**kwargs)
    
    @classmethod
    def get_available_strategies(cls) -> list:
        """Получить список доступных стратегий"""
        return list(cls._strategies.keys())


class ThreadingManager:
    """Менеджер для управления многопоточностью"""
    
    def __init__(self, strategy_type: str = "hybrid", **kwargs):
        self.strategy = ThreadingStrategyFactory.create_strategy(strategy_type, **kwargs)
        self.active_tasks = []
    
    async def execute_task(self, task: Callable, *args, **kwargs) -> Any:
        """Выполнить задачу"""
        return await self.strategy.execute_task(task, *args, **kwargs)
    
    async def execute_tasks_concurrently(self, tasks: List[Callable], *args, **kwargs) -> List[Any]:
        """Выполнить задачи параллельно"""
        return await self.strategy.execute_tasks_concurrently(tasks, *args, **kwargs)
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.strategy.cleanup()
        logger.info("ThreadingManager очищен")
