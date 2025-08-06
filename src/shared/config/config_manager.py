"""
Менеджер конфигурации для централизованного доступа к настройкам
"""
import logging
from typing import Dict, Any, Optional
from .production_config import ProductionConfig


class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self):
        self.config = ProductionConfig()
        self.logger = logging.getLogger(__name__)
        
        # Валидируем конфигурацию при инициализации
        if not self.config.validate():
            self.logger.error("❌ Ошибка валидации конфигурации")
            raise ValueError("Некорректная конфигурация")
        
        self.logger.info("✅ Конфигурация загружена и валидирована")
    
    def get_model_config(self) -> Dict[str, Any]:
        """Получить конфигурацию модели"""
        return self.config.model_config
    
    def get_device_config(self) -> Dict[str, Any]:
        """Получить конфигурацию устройства"""
        return self.config.device_config
    
    def get_services_config(self) -> Dict[str, Any]:
        """Получить конфигурацию сервисов"""
        return self.config.services_config
    
    def get_scraper_config(self) -> Dict[str, Any]:
        """Получить конфигурацию скрапера"""
        return self.config.scraper_config
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Получить конфигурацию производительности"""
        return self.config.performance_config
    
    def get_security_config(self) -> Dict[str, Any]:
        """Получить конфигурацию безопасности"""
        return self.config.security_config
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Получить конфигурацию мониторинга"""
        return self.config.monitoring_config
    
    def get_service_url(self, service_name: str) -> str:
        """Получить URL сервиса"""
        services = self.get_services_config()
        if service_name not in services:
            raise ValueError(f"Сервис {service_name} не найден в конфигурации")
        return services[service_name]
    
    def get_model_path(self) -> str:
        """Получить путь к модели"""
        return self.get_model_config()["path"]
    
    def get_device_type(self) -> str:
        """Получить тип устройства"""
        return self.get_device_config()["type"]
    
    def get_cpu_threads(self) -> int:
        """Получить количество CPU потоков"""
        return self.get_device_config()["cpu_threads"]
    
    def get_gpu_memory_fraction(self) -> float:
        """Получить долю памяти GPU"""
        return self.get_device_config()["gpu_memory_fraction"]
    
    def get_max_generation_time(self) -> int:
        """Получить максимальное время генерации"""
        return self.get_performance_config()["max_generation_time"]
    
    def get_max_workers(self) -> int:
        """Получить максимальное количество воркеров"""
        return self.get_performance_config()["max_workers"]
    
    def get_max_processes(self) -> int:
        """Получить максимальное количество процессов"""
        return self.get_performance_config()["max_processes"]
    
    def get_minjust_url(self) -> str:
        """Получить URL сайта Минюста"""
        return self.get_scraper_config()["minjust_url"]
    
    def get_scraper_delay(self) -> float:
        """Получить задержку скрапера"""
        return self.get_scraper_config()["delay"]
    
    def get_scraper_timeout(self) -> int:
        """Получить таймаут скрапера"""
        return self.get_scraper_config()["timeout"]
    
    def get_max_new_tokens(self) -> int:
        """Получить максимальное количество новых токенов"""
        return self.get_model_config()["max_new_tokens"]
    
    def get_generation_temperature(self) -> float:
        """Получить температуру генерации"""
        return self.get_model_config()["temperature"]
    
    def is_gpu_available(self) -> bool:
        """Проверить доступность GPU"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def should_use_gpu(self) -> bool:
        """Определить, нужно ли использовать GPU"""
        device_type = self.get_device_type()
        if device_type == "gpu":
            return self.is_gpu_available()
        elif device_type == "auto":
            return self.is_gpu_available()
        else:
            return False
    
    def get_optimal_device(self) -> str:
        """Получить оптимальное устройство"""
        if self.should_use_gpu():
            return "cuda"
        else:
            return "cpu"
    
    def log_configuration(self) -> None:
        """Логировать конфигурацию"""
        self.logger.info("📋 Конфигурация системы:")
        self.logger.info(f"   Модель: {self.get_model_path()}")
        self.logger.info(f"   Устройство: {self.get_optimal_device()}")
        self.logger.info(f"   CPU потоков: {self.get_cpu_threads()}")
        self.logger.info(f"   Макс. время генерации: {self.get_max_generation_time()}с")
        self.logger.info(f"   Макс. воркеров: {self.get_max_workers()}")
        self.logger.info(f"   GPU доступен: {self.is_gpu_available()}") 