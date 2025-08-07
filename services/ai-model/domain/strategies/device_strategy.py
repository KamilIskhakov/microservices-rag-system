"""
Стратегии выбора устройства для AI Model Service
"""
from abc import ABC, abstractmethod
import torch
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DeviceStrategy(ABC):
    """Абстрактная стратегия выбора устройства"""
    
    @abstractmethod
    def select_device(self, model_id: str, config: Dict[str, Any] = None) -> str:
        """Выбрать устройство для модели"""
        pass
    
    @abstractmethod
    def is_device_available(self, device: str) -> bool:
        """Проверить доступность устройства"""
        pass


class AutoDeviceStrategy(DeviceStrategy):
    """Автоматический выбор устройства"""
    
    def select_device(self, model_id: str, config: Dict[str, Any] = None) -> str:
        """Автоматически выбрать лучшее доступное устройство"""
        if torch.cuda.is_available():
            logger.info("CUDA доступен, выбираем GPU")
            return "cuda"
        else:
            logger.info("CUDA недоступен, используем CPU")
            return "cpu"
    
    def is_device_available(self, device: str) -> bool:
        """Проверить доступность устройства"""
        if device == "cuda":
            return torch.cuda.is_available()
        elif device == "cpu":
            return True
        return False


class GPUFirstStrategy(DeviceStrategy):
    """Стратегия с приоритетом GPU"""
    
    def select_device(self, model_id: str, config: Dict[str, Any] = None) -> str:
        """Выбрать GPU если доступен, иначе CPU"""
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory
            required_memory = config.get("required_memory", 0) if config else 0
            
            if gpu_memory >= required_memory:
                logger.info(f"GPU выбран, доступно памяти: {gpu_memory / 1024**3:.2f}GB")
                return "cuda"
            else:
                logger.warning(f"GPU памяти недостаточно, используем CPU")
                return "cpu"
        return "cpu"
    
    def is_device_available(self, device: str) -> bool:
        """Проверить доступность устройства"""
        if device == "cuda":
            return torch.cuda.is_available()
        elif device == "cpu":
            return True
        return False


class CPUOnlyStrategy(DeviceStrategy):
    """Стратегия только CPU"""
    
    def select_device(self, model_id: str, config: Dict[str, Any] = None) -> str:
        """Всегда использовать CPU"""
        logger.info("Используем CPU стратегию")
        return "cpu"
    
    def is_device_available(self, device: str) -> bool:
        """Проверить доступность устройства"""
        return device == "cpu"


class DeviceStrategyFactory:
    """Фабрика для создания стратегий выбора устройства"""
    
    _strategies = {
        "auto": AutoDeviceStrategy,
        "gpu_first": GPUFirstStrategy,
        "cpu_only": CPUOnlyStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_type: str = "auto") -> DeviceStrategy:
        """Создать стратегию по типу"""
        strategy_class = cls._strategies.get(strategy_type)
        if not strategy_class:
            logger.warning(f"Неизвестная стратегия {strategy_type}, используем auto")
            strategy_class = AutoDeviceStrategy
        
        return strategy_class()
    
    @classmethod
    def get_available_strategies(cls) -> list:
        """Получить список доступных стратегий"""
        return list(cls._strategies.keys())
