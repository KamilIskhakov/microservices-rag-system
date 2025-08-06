"""
Фабрика устройств для CPU/GPU
"""
import logging
from typing import Dict, Any
from abc import ABC, abstractmethod

from src.shared.config.config_manager import ConfigManager


class DeviceStrategy(ABC):
    """Абстрактная стратегия устройства"""
    
    @abstractmethod
    def optimize_model(self, model) -> None:
        """Оптимизировать модель для устройства"""
        pass
    
    @abstractmethod
    def configure_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Настроить параметры генерации для устройства"""
        pass
    
    @abstractmethod
    def get_memory_info(self) -> Dict[str, Any]:
        """Получить информацию о памяти устройства"""
        pass
    
    @abstractmethod
    def validate_device(self) -> bool:
        """Проверить доступность устройства"""
        pass


class CPUStrategy(DeviceStrategy):
    """Стратегия для CPU"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def optimize_model(self, model) -> None:
        """Оптимизировать модель для CPU"""
        try:
            import torch
            torch.set_num_threads(self.config.get_cpu_threads())
            model.eval()
            self.logger.info(f"✅ Модель оптимизирована для CPU ({self.config.get_cpu_threads()} потоков)")
        except Exception as e:
            self.logger.error(f"❌ Ошибка оптимизации CPU: {e}")
            raise
    
    def configure_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Настроить параметры генерации для CPU"""
        return {
            **params,
            "max_new_tokens": self.config.get_max_new_tokens(),
            "do_sample": True,
            "temperature": self.config.get_generation_temperature(),
            "num_beams": 1,
            "use_cache": True,
            "repetition_penalty": 1.0,
            "early_stopping": True
        }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Получить информацию о памяти CPU"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "device": "cpu",
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent
            }
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения информации о памяти CPU: {e}")
            return {"device": "cpu", "error": str(e)}
    
    def validate_device(self) -> bool:
        """Проверить доступность CPU"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            min_memory_gb = self.config.get_device_config()["min_memory_gb"]
            available_gb = memory.available / (1024**3)
            
            if available_gb < min_memory_gb:
                self.logger.warning(f"⚠️ Доступно памяти: {available_gb:.2f}GB, требуется: {min_memory_gb}GB")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации CPU: {e}")
            return False


class GPUStrategy(DeviceStrategy):
    """Стратегия для GPU"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def optimize_model(self, model) -> None:
        """Оптимизировать модель для GPU"""
        try:
            import torch
            if not torch.cuda.is_available():
                raise RuntimeError("GPU недоступен")
            
            model.to("cuda")
            torch.cuda.set_per_process_memory_fraction(self.config.get_gpu_memory_fraction())
            model.eval()
            self.logger.info(f"✅ Модель оптимизирована для GPU (память: {self.config.get_gpu_memory_fraction()})")
        except Exception as e:
            self.logger.error(f"❌ Ошибка оптимизации GPU: {e}")
            raise
    
    def configure_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Настроить параметры генерации для GPU"""
        return {
            **params,
            "max_new_tokens": 50,  # Больше токенов для GPU
            "do_sample": True,
            "temperature": 0.7,  # Более креативная генерация
            "num_beams": 4,  # Beam search для лучшего качества
            "use_cache": True,
            "repetition_penalty": 1.1
        }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Получить информацию о памяти GPU"""
        try:
            import torch
            if not torch.cuda.is_available():
                return {"device": "gpu", "error": "GPU недоступен"}
            
            memory_allocated = torch.cuda.memory_allocated()
            memory_reserved = torch.cuda.memory_reserved()
            memory_total = torch.cuda.get_device_properties(0).total_memory
            
            return {
                "device": "gpu",
                "total": memory_total,
                "allocated": memory_allocated,
                "reserved": memory_reserved,
                "available": memory_total - memory_reserved
            }
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения информации о памяти GPU: {e}")
            return {"device": "gpu", "error": str(e)}
    
    def validate_device(self) -> bool:
        """Проверить доступность GPU"""
        try:
            import torch
            if not torch.cuda.is_available():
                self.logger.warning("⚠️ GPU недоступен")
                return False
            
            # Проверяем доступную память GPU
            memory_total = torch.cuda.get_device_properties(0).total_memory
            memory_gb = memory_total / (1024**3)
            min_memory_gb = self.config.get_device_config()["min_memory_gb"]
            
            if memory_gb < min_memory_gb:
                self.logger.warning(f"⚠️ Память GPU: {memory_gb:.2f}GB, требуется: {min_memory_gb}GB")
                return False
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка валидации GPU: {e}")
            return False


class DeviceFactory:
    """Фабрика устройств"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def create_device_strategy(self, device_type: str = None) -> DeviceStrategy:
        """Создать стратегию устройства"""
        if device_type is None:
            device_type = self.config.get_device_type()
        
        if device_type == "cpu":
            return CPUStrategy(self.config)
        elif device_type == "gpu":
            return GPUStrategy(self.config)
        elif device_type == "auto":
            # Автоопределение
            if self.config.should_use_gpu():
                return GPUStrategy(self.config)
            else:
                return CPUStrategy(self.config)
        else:
            raise ValueError(f"Неизвестный тип устройства: {device_type}")
    
    def get_optimal_device_strategy(self) -> DeviceStrategy:
        """Получить оптимальную стратегию устройства"""
        return self.create_device_strategy("auto")
    
    def validate_all_devices(self) -> Dict[str, bool]:
        """Проверить все доступные устройства"""
        results = {}
        
        # Проверяем CPU
        try:
            cpu_strategy = CPUStrategy(self.config)
            results["cpu"] = cpu_strategy.validate_device()
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки CPU: {e}")
            results["cpu"] = False
        
        # Проверяем GPU
        try:
            gpu_strategy = GPUStrategy(self.config)
            results["gpu"] = gpu_strategy.validate_device()
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки GPU: {e}")
            results["gpu"] = False
        
        return results 