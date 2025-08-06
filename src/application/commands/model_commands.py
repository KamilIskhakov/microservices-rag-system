"""
Команды для работы с моделями (Command Pattern)
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from ...domain.entities.model import Model
from ...domain.repositories.model_repository import ModelRepository
from ...domain.strategies.model_loading_strategy import ModelLoadingStrategy
import torch

logger = logging.getLogger(__name__)


@dataclass
class LoadModelCommand:
    """Команда загрузки модели"""
    model_path: str
    device: str
    model_type: str = "qwen"
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class UnloadModelCommand:
    """Команда выгрузки модели"""
    model_id: str


@dataclass
class GenerateResponseCommand:
    """Команда генерации ответа"""
    model_id: str
    prompt: str
    max_length: int = 512
    temperature: float = 0.7


class CommandHandler(ABC):
    """Абстрактный обработчик команд"""
    
    @abstractmethod
    def handle(self, command) -> Any:
        """Обработать команду"""
        pass


class LoadModelCommandHandler(CommandHandler):
    """Обработчик команды загрузки модели"""
    
    def __init__(self, model_repository: ModelRepository, loading_strategy: ModelLoadingStrategy):
        self.model_repository = model_repository
        self.loading_strategy = loading_strategy
    
    def handle(self, command: LoadModelCommand) -> Model:
        """Обработать команду загрузки модели"""
        try:
            logger.info(f"Загружаем модель: {command.model_path} на устройстве: {command.device}")
            
            # Загружаем модель используя стратегию
            model_data = self.loading_strategy.load_model(
                model_path=command.model_path,
                device=command.device
            )
            
            # Создаем объект модели
            from datetime import datetime
            model = Model(
                id="qwen-model_full",
                name="Qwen2.5-3B-Instruct",
                path=command.model_path,
                type="qwen",
                version="2.5-3B-Instruct",
                device=command.device,
                parameters={"model_data": model_data},
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_loaded=True
            )
            
            # Сохраняем в репозиторий
            self.model_repository.save(model)
            
            # Сохраняем загруженные компоненты модели
            if hasattr(self.model_repository, 'loaded_models'):
                self.model_repository.loaded_models[model.id] = model_data
            
            logger.info(f"Модель {model.name} успешно загружена")
            return model
            
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки модели: {e}")


class UnloadModelCommandHandler(CommandHandler):
    """Обработчик команды выгрузки модели"""
    
    def __init__(self, model_repository: ModelRepository, loading_strategy: ModelLoadingStrategy):
        self.model_repository = model_repository
        self.loading_strategy = loading_strategy
    
    def handle(self, command: UnloadModelCommand) -> None:
        """Обработать команду выгрузки модели"""
        try:
            # Находим модель
            model = self.model_repository.find_by_id(command.model_id)
            if not model:
                raise ValueError(f"Модель {command.model_id} не найдена")
            
            # Выгружаем модель
            self.loading_strategy.cleanup()
            
            # Обновляем в репозитории
            model.is_loaded = False
            self.model_repository.save(model)
            
        except Exception as e:
            raise RuntimeError(f"Ошибка выгрузки модели: {e}")


class GenerateResponseCommandHandler(CommandHandler):
    """Обработчик команды генерации ответа"""
    
    def __init__(self, model_repository: ModelRepository):
        self.model_repository = model_repository
    
    def handle(self, command: GenerateResponseCommand) -> str:
        """Обработать команду генерации ответа"""
        try:
            logger.info(f"Начинаем генерацию для модели {command.model_id}")
            
            # Находим модель
            model = self.model_repository.find_by_id(command.model_id)
            if not model:
                raise ValueError(f"Модель {command.model_id} не найдена")
            
            logger.info(f"Модель найдена: {model.name}")
            
            if not model.is_available():
                raise RuntimeError(f"Модель {command.model_id} не загружена")
            
            # Получаем загруженную модель из репозитория
            loaded_model_data = self.model_repository.get_loaded_model(command.model_id)
            if not loaded_model_data:
                raise RuntimeError(f"Загруженная модель {command.model_id} не найдена")
            
            logger.info("Загруженные данные модели получены")
            
            # Получаем модель и токенизатор
            model_obj = loaded_model_data.get("model")
            tokenizer = loaded_model_data.get("tokenizer")
            
            if not model_obj or not tokenizer:
                raise RuntimeError(f"Модель или токенизатор не загружены для {command.model_id}")
            
            logger.info("Модель и токенизатор готовы к использованию")
            
            # Генерируем ответ
            logger.info(f"Токенизируем промпт: {command.prompt[:50]}...")
            inputs = tokenizer(command.prompt, return_tensors="pt")
            
            # Используем device из загруженных данных
            device = loaded_model_data.get("device", "cpu")
            logger.info(f"Используем устройство: {device}")
            
            # Перемещаем на правильное устройство
            if device == "cuda":
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Генерируем ответ с параметрами из рабочей версии
            max_tokens = min(command.max_length, 20)  # Ограничиваем для CPU
            logger.info(f"Начинаем генерацию с параметрами: max_new_tokens={max_tokens}")
            
            # Используем минимальные параметры для отладки
            with torch.no_grad():
                outputs = model_obj.generate(
                    **inputs,
                    max_new_tokens=5,  # Очень короткий ответ для тестирования
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id
                )
            
            logger.info("Генерация завершена, декодируем ответ")
            # Декодируем ответ как в рабочей версии
            response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Извлекаем только новую часть ответа
            prompt_length = len(tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True))
            result = response_text[prompt_length:].strip()
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Ошибка генерации ответа: {e}")


class CommandBus:
    """Шина команд"""
    
    def __init__(self):
        self.handlers: Dict[type, CommandHandler] = {}
    
    def register_handler(self, command_type: type, handler: CommandHandler) -> None:
        """Зарегистрировать обработчик команды"""
        self.handlers[command_type] = handler
    
    def execute(self, command) -> Any:
        """Выполнить команду"""
        command_type = type(command)
        
        if command_type not in self.handlers:
            raise ValueError(f"Обработчик для команды {command_type} не найден")
        
        handler = self.handlers[command_type]
        return handler.handle(command)
    
    def execute_async(self, command) -> Any:
        """Выполнить команду асинхронно"""
        # Здесь можно добавить асинхронное выполнение
        return self.execute(command) 