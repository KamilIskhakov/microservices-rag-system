"""
Продакшн конфигурация с группировкой настроек
"""
from typing import Dict, Any
from .environment_config import EnvironmentConfig


class ProductionConfig:
    """Продакшн конфигурация"""
    
    def __init__(self):
        self.env = EnvironmentConfig()
    
    @property
    def model_config(self) -> Dict[str, Any]:
        """Конфигурация модели"""
        return {
            "path": self.env.MODEL_PATH,
            "name": self.env.MODEL_NAME,
            "type": self.env.MODEL_TYPE,
            "max_new_tokens": self.env.MAX_NEW_TOKENS,
            "temperature": self.env.GENERATION_TEMPERATURE
        }
    
    @property
    def device_config(self) -> Dict[str, Any]:
        """Конфигурация устройства"""
        return {
            "type": self.env.DEVICE_TYPE,
            "cpu_threads": self.env.CPU_THREADS,
            "gpu_memory_fraction": self.env.GPU_MEMORY_FRACTION,
            "max_memory_usage": self.env.MAX_MEMORY_USAGE,
            "min_memory_gb": self.env.MIN_MEMORY_GB
        }
    
    @property
    def services_config(self) -> Dict[str, Any]:
        """Конфигурация сервисов"""
        return {
            "ai_model": self.env.AI_MODEL_URL,
            "vectorstore": self.env.VECTORSTORE_URL,
            "request_processor": self.env.REQUEST_PROCESSOR_URL,
            "api_gateway": self.env.API_GATEWAY_URL,
            "scraper": self.env.SCRAPER_URL,
            "payment": self.env.PAYMENT_URL,
            "redis": self.env.REDIS_URL
        }
    
    @property
    def scraper_config(self) -> Dict[str, Any]:
        """Конфигурация скрапера"""
        return {
            "minjust_url": self.env.MINJUST_URL,
            "delay": self.env.SCRAPER_DELAY,
            "timeout": self.env.SCRAPER_TIMEOUT,
            "max_pages": self.env.SCRAPER_MAX_PAGES
        }
    
    @property
    def performance_config(self) -> Dict[str, Any]:
        """Конфигурация производительности"""
        return {
            "max_generation_time": self.env.MAX_GENERATION_TIME,
            "max_workers": self.env.MAX_WORKERS,
            "max_processes": self.env.MAX_PROCESSES
        }
    
    @property
    def security_config(self) -> Dict[str, Any]:
        """Конфигурация безопасности"""
        return {
            "api_key": self.env.API_KEY,
            "secret_key": self.env.SECRET_KEY
        }
    
    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Конфигурация мониторинга"""
        return {
            "enable_metrics": self.env.ENABLE_METRICS,
            "metrics_port": self.env.METRICS_PORT,
            "log_level": self.env.LOG_LEVEL
        }
    
    def validate(self) -> bool:
        """Валидация конфигурации"""
        try:
            # Проверяем обязательные параметры
            assert self.env.MODEL_PATH, "MODEL_PATH не установлен"
            assert self.env.AI_MODEL_URL, "AI_MODEL_URL не установлен"
            assert self.env.VECTORSTORE_URL, "VECTORSTORE_URL не установлен"
            
            # Проверяем числовые параметры
            assert self.env.CPU_THREADS > 0, "CPU_THREADS должен быть > 0"
            assert 0 < self.env.GPU_MEMORY_FRACTION <= 1, "GPU_MEMORY_FRACTION должен быть от 0 до 1"
            assert self.env.MAX_GENERATION_TIME > 0, "MAX_GENERATION_TIME должен быть > 0"
            
            return True
        except AssertionError as e:
            print(f"Ошибка валидации конфигурации: {e}")
            return False 