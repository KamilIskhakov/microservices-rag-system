"""
Наблюдатели для событий модели (Observer Pattern)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
from enum import Enum


class ModelEventType(Enum):
    """Типы событий модели"""
    MODEL_LOADED = "model_loaded"
    MODEL_UNLOADED = "model_unloaded"
    MODEL_ERROR = "model_error"
    MODEL_MEMORY_USAGE = "model_memory_usage"


class ModelEvent:
    """Событие модели"""
    
    def __init__(self, event_type: ModelEventType, model_id: str, data: Dict[str, Any] = None):
        self.event_type = event_type
        self.model_id = model_id
        self.data = data or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            "event_type": self.event_type.value,
            "model_id": self.model_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class ModelObserver(ABC):
    """Абстрактный наблюдатель событий модели"""
    
    @abstractmethod
    def update(self, event: ModelEvent) -> None:
        """Обновить наблюдателя"""
        pass


class ModelLoadingObserver(ModelObserver):
    """Наблюдатель загрузки модели"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def update(self, event: ModelEvent) -> None:
        """Обработать событие загрузки модели"""
        if event.event_type == ModelEventType.MODEL_LOADED:
            if self.logger:
                self.logger.info(f"Модель {event.model_id} загружена")
            print(f"✅ Модель {event.model_id} загружена")
        
        elif event.event_type == ModelEventType.MODEL_UNLOADED:
            if self.logger:
                self.logger.info(f"Модель {event.model_id} выгружена")
            print(f"🔄 Модель {event.model_id} выгружена")
        
        elif event.event_type == ModelEventType.MODEL_ERROR:
            error_msg = event.data.get("error", "Неизвестная ошибка")
            if self.logger:
                self.logger.error(f"Ошибка модели {event.model_id}: {error_msg}")
            print(f"❌ Ошибка модели {event.model_id}: {error_msg}")


class ModelMemoryObserver(ModelObserver):
    """Наблюдатель использования памяти модели"""
    
    def __init__(self, memory_threshold: int = 1024 * 1024 * 1024):  # 1GB
        self.memory_threshold = memory_threshold
        self.memory_usage = {}
    
    def update(self, event: ModelEvent) -> None:
        """Обработать событие использования памяти"""
        if event.event_type == ModelEventType.MODEL_MEMORY_USAGE:
            memory_usage = event.data.get("memory_usage", 0)
            self.memory_usage[event.model_id] = memory_usage
            
            if memory_usage > self.memory_threshold:
                print(f"⚠️ Высокое использование памяти моделью {event.model_id}: {memory_usage / 1024 / 1024:.2f}MB")


class ModelPerformanceObserver(ModelObserver):
    """Наблюдатель производительности модели"""
    
    def __init__(self):
        self.performance_metrics = {}
    
    def update(self, event: ModelEvent) -> None:
        """Обработать событие производительности"""
        if event.event_type == ModelEventType.MODEL_LOADED:
            model_id = event.model_id
            load_time = event.data.get("load_time", 0)
            
            if model_id not in self.performance_metrics:
                self.performance_metrics[model_id] = {}
            
            self.performance_metrics[model_id]["load_time"] = load_time
            print(f"📊 Время загрузки модели {model_id}: {load_time:.2f}с")


class ModelEventManager:
    """Менеджер событий модели"""
    
    def __init__(self):
        self.observers: List[ModelObserver] = []
    
    def add_observer(self, observer: ModelObserver) -> None:
        """Добавить наблюдателя"""
        self.observers.append(observer)
    
    def remove_observer(self, observer: ModelObserver) -> None:
        """Удалить наблюдателя"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_observers(self, event: ModelEvent) -> None:
        """Уведомить всех наблюдателей"""
        for observer in self.observers:
            try:
                observer.update(event)
            except Exception as e:
                print(f"Ошибка в наблюдателе: {e}")
    
    def create_event(self, event_type: ModelEventType, model_id: str, data: Dict[str, Any] = None) -> ModelEvent:
        """Создать событие"""
        event = ModelEvent(event_type, model_id, data)
        self.notify_observers(event)
        return event 