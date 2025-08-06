"""
Фабрика для создания моделей (Factory Pattern)
"""
from typing import Dict, Any
from datetime import datetime
import uuid
from ..entities.model import Model


class ModelFactory:
    """Фабрика для создания моделей"""
    
    @staticmethod
    def create_qwen_model(
        path: str,
        device: str = "cpu",
        version: str = "1.0.0",
        parameters: Dict[str, Any] = None
    ) -> Model:
        """Создать модель Qwen"""
        if parameters is None:
            parameters = {
                "max_length": 512,
                "temperature": 0.7,
                "top_p": 0.9
            }
        
        return Model(
            id=str(uuid.uuid4()),
            name="Qwen",
            path=path,
            type="qwen",
            version=version,
            device=device,
            parameters=parameters,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @staticmethod
    def create_gpt_model(
        path: str,
        device: str = "cpu",
        version: str = "1.0.0",
        parameters: Dict[str, Any] = None
    ) -> Model:
        """Создать модель GPT"""
        if parameters is None:
            parameters = {
                "max_length": 512,
                "temperature": 0.7,
                "top_p": 0.9
            }
        
        return Model(
            id=str(uuid.uuid4()),
            name="GPT",
            path=path,
            type="gpt",
            version=version,
            device=device,
            parameters=parameters,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @staticmethod
    def create_model(
        model_type: str,
        path: str,
        device: str = "cpu",
        version: str = "1.0.0",
        parameters: Dict[str, Any] = None
    ) -> Model:
        """Создать модель по типу"""
        if model_type.lower() == "qwen":
            return ModelFactory.create_qwen_model(path, device, version, parameters)
        elif model_type.lower() == "gpt":
            return ModelFactory.create_gpt_model(path, device, version, parameters)
        else:
            raise ValueError(f"Неизвестный тип модели: {model_type}")
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> Model:
        """Создать модель из конфигурации"""
        required_fields = ["type", "path", "name"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Отсутствует обязательное поле: {field}")
        
        return ModelFactory.create_model(
            model_type=config["type"],
            path=config["path"],
            device=config.get("device", "cpu"),
            version=config.get("version", "1.0.0"),
            parameters=config.get("parameters", {})
        ) 