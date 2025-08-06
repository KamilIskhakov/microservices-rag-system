"""
Логгер для всех сервисов
"""
import logging
import sys
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Форматтер с цветным выводом"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Добавляем цвет к уровню логирования
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logger(name: str, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Настройка логгера"""
    
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Очищаем существующие обработчики
    logger.handlers.clear()
    
    # Создаем форматтер
    formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Обработчик для файла (если указан)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Создаем основной логгер
logger = setup_logger("rag_service")

def get_logger(name: str) -> logging.Logger:
    """Получение логгера по имени"""
    return logging.getLogger(name)

class LoggerMixin:
    """Миксин для добавления логгера к классам"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)
    
    def log_info(self, message: str):
        """Логирование информационного сообщения"""
        self.logger.info(message)
    
    def log_error(self, message: str, exc_info: bool = True):
        """Логирование ошибки"""
        self.logger.error(message, exc_info=exc_info)
    
    def log_warning(self, message: str):
        """Логирование предупреждения"""
        self.logger.warning(message)
    
    def log_debug(self, message: str):
        """Логирование отладочной информации"""
        self.logger.debug(message) 