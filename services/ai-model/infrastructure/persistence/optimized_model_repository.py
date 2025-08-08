"""
Оптимизированная реализация репозитория моделей для AI Model Service
"""
import os
import logging
import time
import psutil
import torch
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from transformers import AutoTokenizer, AutoModelForCausalLM
from domain.repositories.model_repository import ModelRepository
from domain.entities.model import Model
from domain.factories.model_factory import ModelFactoryRegistry
from domain.strategies.threading_strategy import ThreadingManager

logger = logging.getLogger(__name__)


class OptimizedModelRepository(ModelRepository):
    """Оптимизированная реализация репозитория моделей"""
    
    def __init__(self, factory_name: str = "optimized", threading_strategy: str = "async"):
        self.models: Dict[str, Model] = {}
        self.loaded_models: Dict[str, Any] = {}  # model_id -> (tokenizer, model)
        
        self.model_factory = ModelFactoryRegistry.get_factory(factory_name)
        self.threading_manager = ThreadingManager(threading_strategy)
        
        logger.info(f"Инициализирован OptimizedModelRepository с фабрикой {factory_name} и стратегией {threading_strategy}")
    
    def _setup_model_paths(self):
        """Настройка путей к моделям (устаревший метод)"""
        pass
    
    def save(self, model: Model) -> Model:
        """Сохранить модель"""
        self.models[model.id] = model
        return model
    
    def find_by_id(self, model_id: str) -> Optional[Model]:
        """Найти модель по ID"""
        return self.models.get(model_id)
    
    def find_all(self) -> List[Model]:
        """Найти все модели"""
        return list(self.models.values())
    
    def find_loaded_models(self) -> List[Model]:
        """Найти все загруженные модели"""
        return [model for model in self.models.values() if model.is_loaded]
    
    def delete(self, model_id: str) -> bool:
        """Удалить модель"""
        if model_id in self.models:
            if model_id in self.loaded_models:
                self.unload_model(model_id)
            del self.models[model_id]
            return True
        return False
    
    async def load_model(self, model_id: str, device: str = "auto") -> Model:
        """Загрузить модель в память с использованием фабрики"""
        try:
            logger.info(f"Загружаем модель: {model_id}")
            
            if not self.model_factory.validate_model(model_id):
                raise ValueError(f"Модель {model_id} не найдена или недоступна")
            
            config = self.model_factory.get_model_config(model_id)
            if device == "auto":
                config["device"] = device
            
            tokenizer, model = await self.threading_manager.execute_task(
                self.model_factory.create_model,
                model_id,
                config
            )
            
            self.loaded_models[model_id] = (tokenizer, model)
            
            model_path = self.model_factory.model_paths[model_id]
            model_entity = self.model_factory.create_model_entity(model_id, model.device, model_path)
            self.models[model_id] = model_entity
            
            logger.info(f"Модель {model_id} успешно загружена на {model.device}")
            return self.models[model_id]
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели {model_id}: {e}")
            raise
    
    def unload_model(self, model_id: str) -> bool:
        """Выгрузить модель из памяти"""
        try:
            if model_id in self.loaded_models:
                tokenizer, model = self.loaded_models[model_id]
                del tokenizer
                del model
                del self.loaded_models[model_id]
                
                if model_id in self.models:
                    self.models[model_id].unload()
                
                logger.info(f"Модель {model_id} выгружена")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка выгрузки модели {model_id}: {e}")
            return False
    
    def _generate_text_sync(self, model_id: str, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        """Генерировать текст с помощью модели"""
        if model_id not in self.loaded_models:
            raise ValueError(f"Модель {model_id} не загружена")
        
        try:
            tokenizer, model = self.loaded_models[model_id]
            
            inputs = tokenizer(
                prompt, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=max_length
            )
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=10,
                    do_sample=True,
                    temperature=temperature,
                    pad_token_id=tokenizer.eos_token_id,
                    num_beams=1,
                    repetition_penalty=1.0,
                    use_cache=True,
                    eos_token_id=tokenizer.eos_token_id,
                    early_stopping=True
                )
            
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Ошибка генерации текста: {e}")
            raise
    
    async def generate_text(self, model_id: str, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        return await self.threading_manager.execute_task(
            self._generate_text_sync,
            model_id,
            prompt,
            max_length,
            temperature
        )

    def get_memory_usage(self) -> Dict[str, Any]:
        """Получить информацию об использовании памяти"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "loaded_models_count": len(self.loaded_models)
        }
    
    def optimize_memory(self) -> None:
        """Оптимизировать использование памяти"""
        try:
            import gc
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Память оптимизирована")
        except Exception as e:
            logger.error(f"Ошибка оптимизации памяти: {e}")
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о модели"""
        if model_id not in self.models:
            return None
        
        model = self.models[model_id]
        memory_usage = self.get_memory_usage()
        
        return {
            "id": model.id,
            "name": model.name,
            "type": model.type,
            "device": model.device,
            "is_loaded": model.is_loaded,
            "path": model.path,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
            "memory_usage": memory_usage
        }
