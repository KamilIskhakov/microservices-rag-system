"""
Стратегии загрузки моделей
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)

class ModelLoadingStrategy(ABC):
    """Абстрактная стратегия загрузки модели"""
    
    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> Any:
        """Загружает модель"""
        pass
    
    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """Возвращает информацию об устройстве"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Очищает ресурсы"""
        pass

class CPUModelLoadingStrategy(ModelLoadingStrategy):
    """Стратегия загрузки модели на CPU"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
    
    def load_model(self, model_path: str, **kwargs) -> Any:
        """Загружает модель на CPU"""
        logger.info(f"Loading model on CPU: {model_path}")
        
        try:
            # Загружаем токенизатор
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            logger.info("Tokenizer loaded successfully on CPU")
            
            # Загружаем модель
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                trust_remote_code=True
            )
            logger.info("Model loaded successfully on CPU")
            
            return {
                "device": "cpu",
                "model": self.model,
                "tokenizer": self.tokenizer,
                "model_path": model_path
            }
            
        except Exception as e:
            logger.error(f"Error loading model on CPU: {e}")
            raise
    
    def get_device_info(self) -> Dict[str, Any]:
        """Возвращает информацию об устройстве"""
        return {
            "device": "cpu",
            "cpu_count": torch.get_num_threads(),
            "memory_available": torch.get_num_threads() * 1024 * 1024 * 1024
        }
    
    def cleanup(self):
        """Очищает ресурсы CPU"""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        
        logger.info("CPU model cleanup completed")

class GPUModelLoadingStrategy(ModelLoadingStrategy):
    """Стратегия загрузки модели на GPU"""
    
    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.model = None
        self.tokenizer = None
    
    def load_model(self, model_path: str, **kwargs) -> Any:
        """Загружает модель на GPU"""
        logger.info(f"Loading model on GPU {self.device_id}: {model_path}")
        
        try:
            # Загружаем токенизатор
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            logger.info("Tokenizer loaded successfully on GPU")
            
            # Загружаем модель
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            logger.info("Model loaded successfully on GPU")
            
            return {
                "device": "cuda",
                "model": self.model,
                "tokenizer": self.tokenizer,
                "model_path": model_path,
                "gpu_id": self.device_id
            }
            
        except Exception as e:
            logger.error(f"Error loading model on GPU: {e}")
            raise
    
    def get_device_info(self) -> Dict[str, Any]:
        """Возвращает информацию об устройстве"""
        return {
            "device": "cuda",
            "gpu_name": torch.cuda.get_device_name(self.device_id),
            "gpu_memory": torch.cuda.get_device_properties(self.device_id).total_memory,
            "gpu_count": torch.cuda.device_count()
        }
    
    def cleanup(self):
        """Очищает ресурсы GPU"""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        
        torch.cuda.empty_cache()
        logger.info("GPU model cleanup completed")

class ModelLoadingStrategyFactory:
    """Фабрика для создания стратегий загрузки моделей"""
    
    @staticmethod
    def create_strategy(device: str = "auto") -> ModelLoadingStrategy:
        """Создает стратегию загрузки модели"""
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if device == "cuda" and torch.cuda.is_available():
            logger.info("Creating GPU model loading strategy")
            return GPUModelLoadingStrategy()
        else:
            logger.info("Creating CPU model loading strategy")
            return CPUModelLoadingStrategy() 