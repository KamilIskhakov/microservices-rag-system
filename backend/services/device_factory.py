from abc import ABC, abstractmethod
import torch
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .logger import logger

@dataclass
class DeviceConfig:
    """Конфигурация устройства"""
    device: str
    dtype: torch.dtype
    memory_efficient: bool = True
    max_memory: Optional[float] = None

class DeviceFactory(ABC):
    """Абстрактная фабрика устройств"""
    
    @abstractmethod
    def create_device(self) -> DeviceConfig:
        """Создает конфигурацию устройства"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Проверяет доступность устройства"""
        pass

class CUDADeviceFactory(DeviceFactory):
    """Фабрика для CUDA устройств"""
    
    def is_available(self) -> bool:
        return torch.cuda.is_available()
    
    def create_device(self) -> DeviceConfig:
        if not self.is_available():
            logger.error("CUDA недоступна")
            raise RuntimeError("CUDA недоступна")
        
        config = DeviceConfig(
            device="cuda",
            dtype=torch.float16,
            memory_efficient=True,
            max_memory=0.8
        )
        
        logger.device_info("CUDA", {
            "device": config.device,
            "dtype": str(config.dtype),
            "memory_efficient": config.memory_efficient,
            "max_memory": config.max_memory
        })
        
        return config

class MPSDeviceFactory(DeviceFactory):
    """Фабрика для Apple Silicon MPS"""
    
    def is_available(self) -> bool:
        return torch.backends.mps.is_available()
    
    def create_device(self) -> DeviceConfig:
        if not self.is_available():
            logger.error("MPS недоступен")
            raise RuntimeError("MPS недоступен")
        
        config = DeviceConfig(
            device="mps",
            dtype=torch.float16,
            memory_efficient=True,
            max_memory=0.8
        )
        
        logger.device_info("Apple Silicon MPS", {
            "device": config.device,
            "dtype": str(config.dtype),
            "memory_efficient": config.memory_efficient,
            "max_memory": config.max_memory
        })
        
        return config

class CPUDeviceFactory(DeviceFactory):
    """Фабрика для CPU устройств"""
    
    def is_available(self) -> bool:
        return True  # CPU всегда доступен
    
    def create_device(self) -> DeviceConfig:
        config = DeviceConfig(
            device="cpu",
            dtype=torch.float32,
            memory_efficient=False,
            max_memory=None
        )
        
        logger.device_info("CPU", {
            "device": config.device,
            "dtype": str(config.dtype),
            "memory_efficient": config.memory_efficient
        })
        
        return config

class DeviceManager:
    """Менеджер устройств с приоритетом"""
    
    def __init__(self):
        self.factories = [
            CUDADeviceFactory(),
            MPSDeviceFactory(),
            CPUDeviceFactory()
        ]
        logger.info("DeviceManager initialized")
    
    def get_optimal_device(self) -> DeviceConfig:
        """Возвращает оптимальное устройство по приоритету"""
        for factory in self.factories:
            if factory.is_available():
                try:
                    device_config = factory.create_device()
                    logger.info(f"Selected device: {device_config.device}")
                    return device_config
                except Exception as e:
                    logger.warning(f"Ошибка инициализации {factory.__class__.__name__}: {e}")
                    continue
        
        # Fallback на CPU
        logger.warning("Using CPU fallback")
        return CPUDeviceFactory().create_device()
    
    def get_device_info(self) -> Dict[str, Any]:
        """Возвращает информацию о доступных устройствах"""
        info = {
            "cuda_available": torch.cuda.is_available(),
            "mps_available": torch.backends.mps.is_available(),
            "cpu_available": True,
            "selected_device": None
        }
        
        try:
            device_config = self.get_optimal_device()
            info["selected_device"] = {
                "type": device_config.device,
                "dtype": str(device_config.dtype),
                "memory_efficient": device_config.memory_efficient
            }
            logger.info(f"Device info: {info}")
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            info["error"] = str(e)
        
        return info 