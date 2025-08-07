"""
Фабрика для создания моделей в AI Model Service
"""
import os
import logging
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from ..entities.model import Model
from ..strategies.device_strategy import DeviceStrategyFactory, DeviceStrategy

logger = logging.getLogger(__name__)


class ModelFactory(ABC):
    """Абстрактная фабрика для создания моделей"""
    
    @abstractmethod
    def create_model(self, model_id: str, config: Dict[str, Any] = None) -> Tuple[Any, Any]:
        """Создать модель и токенизатор"""
        pass
    
    @abstractmethod
    def create_model_entity(self, model_id: str, device: str, path: str) -> Model:
        """Создать доменную сущность модели"""
        pass


class OptimizedModelFactory(ModelFactory):
    """Оптимизированная фабрика для создания моделей"""
    
    def __init__(self, device_strategy: DeviceStrategy = None):
        self.device_strategy = device_strategy or DeviceStrategyFactory.create_strategy()
        self.model_paths = self._setup_model_paths()
    
    def _setup_model_paths(self) -> Dict[str, str]:
        """Настройка путей к моделям"""
        base_path = "/app/models"
        return {
            "qwen-model_full": os.path.join(base_path, "qwen-model_full"),
            # Добавьте другие модели по необходимости
        }
    
    def create_model(self, model_id: str, config: Dict[str, Any] = None) -> Tuple[Any, Any]:
        """Создать модель и токенизатор с оптимизацией"""
        try:
            # Проверяем доступность модели
            if model_id not in self.model_paths:
                raise ValueError(f"Модель {model_id} не найдена в конфигурации")
            
            model_path = self.model_paths[model_id]
            if not os.path.exists(model_path):
                raise ValueError(f"Путь к модели не существует: {model_path}")
            
            # Выбираем устройство
            device = self.device_strategy.select_device(model_id, config)
            
            logger.info(f"Создаем модель {model_id} на устройстве {device}")
            
            # Загружаем токенизатор
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # Загружаем модель с оптимизациями
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                device_map=device,
                low_cpu_mem_usage=True
            )
            
            # Оптимизации для GPU
            if device == "cuda":
                model = model.half()  # Используем float16 для экономии памяти
                torch.cuda.empty_cache()
            
            logger.info(f"Модель {model_id} успешно создана на {device}")
            return tokenizer, model
            
        except Exception as e:
            logger.error(f"Ошибка создания модели {model_id}: {e}")
            raise
    
    def create_model_entity(self, model_id: str, device: str, path: str) -> Model:
        """Создать доменную сущность модели"""
        from datetime import datetime
        
        return Model(
            id=model_id,
            name=model_id,
            type="causal_lm",
            device=device,
            is_loaded=True,
            path=path,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def get_model_config(self, model_id: str) -> Dict[str, Any]:
        """Получить конфигурацию модели"""
        configs = {
            "qwen-model_full": {
                "max_length": 512,
                "temperature": 0.7,
                "required_memory": 8 * 1024**3,  # 8GB
                "model_type": "causal_lm"
            }
        }
        return configs.get(model_id, {})
    
    def validate_model(self, model_id: str) -> bool:
        """Проверить валидность модели"""
        return model_id in self.model_paths and os.path.exists(self.model_paths[model_id])


class ModelFactoryRegistry:
    """Реестр фабрик моделей"""
    
    _factories: Dict[str, ModelFactory] = {}
    
    @classmethod
    def register_factory(cls, name: str, factory: ModelFactory):
        """Зарегистрировать фабрику"""
        cls._factories[name] = factory
        logger.info(f"Зарегистрирована фабрика моделей: {name}")
    
    @classmethod
    def get_factory(cls, name: str = "optimized") -> ModelFactory:
        """Получить фабрику по имени"""
        factory = cls._factories.get(name)
        if not factory:
            logger.warning(f"Фабрика {name} не найдена, используем optimized")
            factory = OptimizedModelFactory()
            cls.register_factory("optimized", factory)
        
        return factory
    
    @classmethod
    def get_available_factories(cls) -> list:
        """Получить список доступных фабрик"""
        return list(cls._factories.keys())


# Регистрируем фабрики по умолчанию
ModelFactoryRegistry.register_factory("optimized", OptimizedModelFactory())
