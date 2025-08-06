"""
Оптимизированная реализация репозитория моделей
"""
import os
import torch
import psutil
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ...domain.repositories.model_repository import ModelRepository
from ...domain.entities.model import Model
from ...domain.factories.model_factory import ModelFactory
from ...domain.strategies.model_loading_strategy import ModelLoadingStrategyFactory
from ...domain.observers.model_observer import ModelEventManager, ModelEventType


class OptimizedModelRepository(ModelRepository):
    """Оптимизированная реализация репозитория моделей"""
    
    def __init__(self, event_manager: ModelEventManager = None):
        self.models: Dict[str, Model] = {}
        self.loaded_models: Dict[str, Any] = {}  # torch models
        self.event_manager = event_manager or ModelEventManager()
        self.logger = logging.getLogger(__name__)
        
        # Добавляем наблюдателей
        from ...domain.observers.model_observer import ModelLoadingObserver, ModelMemoryObserver
        self.event_manager.add_observer(ModelLoadingObserver(self.logger))
        self.event_manager.add_observer(ModelMemoryObserver())
    
    def save(self, model: Model) -> None:
        """Сохранить модель"""
        self.models[model.id] = model
        self.logger.info(f"Модель {model.id} сохранена")
    
    def find_by_id(self, model_id: str) -> Optional[Model]:
        """Найти модель по ID"""
        return self.models.get(model_id)
    
    def find_by_name(self, name: str) -> Optional[Model]:
        """Найти модель по имени"""
        for model in self.models.values():
            if model.name == name:
                return model
        return None
    
    def find_all(self) -> List[Model]:
        """Найти все модели"""
        return list(self.models.values())
    
    def find_loaded_models(self) -> List[Model]:
        """Найти все загруженные модели"""
        return [model for model in self.models.values() if model.is_loaded]
    
    def load_model(self, model_path: str, device: str = "auto") -> Model:
        """Загрузить модель с оптимизацией памяти"""
        try:
            # Проверяем существование файла
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Файл модели не найден: {model_path}")
            
            # Проверяем доступную память
            self._check_memory_availability()
            
            # Создаем стратегию загрузки
            loading_strategy = ModelLoadingStrategyFactory.create_strategy(device)
            
            # Засекаем время загрузки
            start_time = datetime.now()
            
            # Загружаем модель через стратегию с оптимизацией CPU
            model_data = loading_strategy.load_model(model_path, device=device)
            
            # Оптимизируем модель для CPU
            if isinstance(model_data, dict) and 'model' in model_data:
                model_instance = model_data['model']
                # Устанавливаем количество потоков для CPU
                torch.set_num_threads(4)
                # Включаем оптимизации для CPU
                model_instance.eval()  # Режим оценки
                if hasattr(model_instance, 'config'):
                    model_instance.config.use_cache = True
            
            # Вычисляем время загрузки
            load_time = (datetime.now() - start_time).total_seconds()
            
            # Создаем объект модели
            model = Model(
                id="qwen-model_full",
                name="Qwen2.5-3B-Instruct",
                type="causal_lm",
                device=device,
                is_loaded=True,
                path=model_path,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Сохраняем модель
            self.save(model)
            
            # Сохраняем загруженные компоненты
            self.loaded_models[model.id] = model_data
            
            # Уведомляем наблюдателей
            self.event_manager.create_event(
                ModelEventType.MODEL_LOADED,
                model.id,
                {"load_time": load_time, "device": device, "path": model_path}
            )
            
            self.logger.info(f"Модель {model.id} загружена за {load_time:.2f}с")
            return model
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели {model_path}: {e}")
            
            # Уведомляем об ошибке
            self.event_manager.create_event(
                ModelEventType.MODEL_ERROR,
                "unknown",
                {"error": str(e), "path": model_path}
            )
            
            raise
    
    def unload_model(self, model_id: str) -> None:
        """Выгрузить модель из памяти"""
        try:
            model = self.find_by_id(model_id)
            if not model:
                raise ValueError(f"Модель {model_id} не найдена")
            
            # Создаем стратегию загрузки
            loading_strategy = ModelLoadingStrategyFactory.create_strategy(model.device)
            
            # Выгружаем модель
            loading_strategy.unload(model)
            
            # Уведомляем наблюдателей
            self.event_manager.create_event(
                ModelEventType.MODEL_UNLOADED,
                model.id,
                {"device": model.device}
            )
            
            self.logger.info(f"Модель {model_id} выгружена")
            
        except Exception as e:
            self.logger.error(f"Ошибка выгрузки модели {model_id}: {e}")
            raise
    
    def delete(self, model_id: str) -> None:
        """Удалить модель"""
        try:
            # Сначала выгружаем модель
            if model_id in self.models and self.models[model_id].is_loaded:
                self.unload_model(model_id)
            
            # Удаляем из словаря
            if model_id in self.models:
                del self.models[model_id]
            
            self.logger.info(f"Модель {model_id} удалена")
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления модели {model_id}: {e}")
            raise
    
    def _check_memory_availability(self) -> None:
        """Проверить доступность памяти"""
        memory = psutil.virtual_memory()
        available_memory = memory.available
        
        # Минимально необходимое количество памяти (2GB)
        min_required = 2 * 1024 * 1024 * 1024
        
        if available_memory < min_required:
            raise RuntimeError(
                f"Недостаточно памяти. Доступно: {available_memory / 1024 / 1024 / 1024:.2f}GB, "
                f"Требуется минимум: {min_required / 1024 / 1024 / 1024:.2f}GB"
            )
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Получить информацию об использовании памяти"""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent,
            "loaded_models_count": len(self.find_loaded_models())
        }
    
    def optimize_memory(self) -> None:
        """Оптимизировать использование памяти"""
        # Очищаем кэш PyTorch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Принудительная сборка мусора
        import gc
        gc.collect()
        
        self.logger.info("Память оптимизирована")
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Получить подробную информацию о модели"""
        model = self.find_by_id(model_id)
        if not model:
            return None
        
        info = model.get_info()
        info["memory_usage"] = self.get_memory_usage()
        return info 
    
    def get_loaded_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Получить загруженную модель"""
        return self.loaded_models.get(model_id)
    
    def get_device_info(self) -> Dict[str, Any]:
        """Получить информацию об устройстве"""
        memory = psutil.virtual_memory()
        return {
            "device": "cpu",  # По умолчанию CPU
            "cpu_count": os.cpu_count(),
            "memory_available": memory.available,
            "total_memory": memory.total
        } 
    
    def generate_text(self, model_id: str, prompt: str, max_length: int = 512, temperature: float = 0.7) -> str:
        """Генерировать текст"""
        try:
            model = self.find_by_id(model_id)
            if not model or not model.is_loaded:
                raise ValueError(f"Модель {model_id} не загружена")
            
            # Получаем загруженную модель
            if model_id not in self.loaded_models:
                raise ValueError(f"Модель {model_id} не найдена в памяти")
            
            model_data = self.loaded_models[model_id]
            
            # Генерируем текст через transformers
            if isinstance(model_data, dict) and 'model' in model_data and 'tokenizer' in model_data:
                tokenizer = model_data['tokenizer']
                model_instance = model_data['model']
                
                # Токенизируем входной текст с attention_mask
                inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
                
                # Генерируем текст с максимальной оптимизацией для CPU
                with torch.no_grad():
                    # Устанавливаем количество потоков для CPU
                    torch.set_num_threads(4)  # Используем 4 потока для CPU
                    
                    outputs = model_instance.generate(
                        inputs.input_ids,
                        attention_mask=inputs.attention_mask,
                        max_new_tokens=10,  # Минимальный ответ
                        do_sample=True,  # Включаем sampling
                        temperature=0.1,  # Низкая температура
                        pad_token_id=tokenizer.eos_token_id,
                        num_beams=1,  # Отключаем beam search для скорости
                        repetition_penalty=1.0,  # Отключаем penalty для скорости
                        use_cache=True,  # Включаем кэш для скорости
                        eos_token_id=tokenizer.eos_token_id,  # Принудительная остановка
                        early_stopping=True  # Останавливаем при EOS
                    )
                
                # Декодируем результат
                generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                return generated_text
            else:
                raise ValueError(f"Неподдерживаемый формат модели {model_id}")
                
        except Exception as e:
            self.logger.error(f"Ошибка генерации текста: {e}")
            raise 