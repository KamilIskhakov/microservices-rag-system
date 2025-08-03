import logging
import sys
from typing import Optional
from pathlib import Path

class RAGLogger:
    """Система логирования для RAG сервиса"""
    
    def __init__(self, name: str = "rag_service", log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Создаем форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Консольный обработчик
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Файловый обработчик
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "rag_service.log", encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Отдельный файл для ошибок
        error_handler = logging.FileHandler(log_dir / "errors.log", encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def info(self, message: str):
        """Информационное сообщение"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Предупреждение"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Ошибка"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Отладочное сообщение"""
        self.logger.debug(message)
    
    def critical(self, message: str):
        """Критическая ошибка"""
        self.logger.critical(message)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Логирование производительности"""
        extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.info(f"PERFORMANCE: {operation} took {duration:.2f}s {extra_info}")
    
    def device_info(self, device_type: str, device_config: dict):
        """Логирование информации об устройстве"""
        self.info(f"DEVICE: Using {device_type} with config: {device_config}")
    
    def model_loading(self, model_path: str, device: str):
        """Логирование загрузки модели"""
        self.info(f"MODEL: Loading {model_path} on {device}")
    
    def request_processing(self, query: str, processing_time: float, result: str):
        """Логирование обработки запроса"""
        # Очищаем чувствительные данные из запроса
        try:
            from middleware.security import security_middleware
            sanitized_query = security_middleware.sanitize_log_data(query)
        except ImportError:
            sanitized_query = query[:50] + "..." if len(query) > 50 else query
        
        self.info(f"REQUEST: '{sanitized_query}' -> {result} ({processing_time:.2f}s)")
    
    def cache_hit(self, cache_key: str):
        """Логирование попадания в кэш"""
        self.info(f"CACHE: Hit for key: {cache_key[:30]}...")
    
    def cache_miss(self, cache_key: str):
        """Логирование промаха кэша"""
        self.info(f"CACHE: Miss for key: {cache_key[:30]}...")

# Глобальный экземпляр логгера
logger = RAGLogger() 