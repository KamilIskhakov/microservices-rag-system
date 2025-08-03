import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Optional, Dict, Any
import threading
import time
from .device_factory import DeviceManager, DeviceConfig
from .logger import logger

class ModelManager:
    """Менеджер моделей с кэшированием и многопоточностью"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.device_manager = DeviceManager()
        self.device_config = self.device_manager.get_optimal_device()
        
        # Кэш для моделей
        self._tokenizer: Optional[AutoTokenizer] = None
        self._model: Optional[AutoModelForCausalLM] = None
        self._lock = threading.Lock()
        self._last_used = 0
        self._cache_timeout = 300  # 5 минут
        
        logger.info(f"ModelManager initialized for {model_path}")
        logger.device_info(self.device_config.device, {
            "dtype": str(self.device_config.dtype),
            "memory_efficient": self.device_config.memory_efficient
        })
    
    def _load_model(self):
        """Загружает модель с оптимизациями"""
        with self._lock:
            if self._model is not None:
                return
            
            start_time = time.time()
            logger.model_loading(self.model_path, self.device_config.device)
            
            try:
                # Загружаем токенизатор
                logger.info("Loading tokenizer...")
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_path,
                    local_files_only=True
                )
                
                # Оптимизации для разных устройств
                if self.device_config.device == "mps":
                    torch.backends.mps.enable_fallback_to_cpu = True
                    logger.info("Applied MPS optimizations")
                elif self.device_config.device == "cuda":
                    torch.backends.cuda.matmul.allow_tf32 = True
                    torch.backends.cudnn.allow_tf32 = True
                    logger.info("Applied CUDA optimizations")
                
                # Загружаем модель
                logger.info("Loading model...")
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=self.device_config.dtype,
                    low_cpu_mem_usage=self.device_config.memory_efficient,
                    local_files_only=True
                )
                
                # Перемещаем на устройство
                logger.info(f"Moving model to {self.device_config.device}")
                self._model.to(self.device_config.device)
                
                # Дополнительные оптимизации
                if self.device_config.device in ["cuda", "mps"]:
                    self._model.eval()
                
                load_time = time.time() - start_time
                logger.performance("Model loading", load_time, device=self.device_config.device)
                logger.info(f"Model loaded successfully on {self.device_config.device}")
                
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                raise
    
    def get_tokenizer(self) -> AutoTokenizer:
        """Возвращает токенизатор"""
        if self._tokenizer is None:
            self._load_model()
        return self._tokenizer
    
    def get_model(self) -> AutoModelForCausalLM:
        """Возвращает модель"""
        if self._model is None:
            self._load_model()
        self._last_used = time.time()
        return self._model
    
    def generate_response(self, prompt: str, max_tokens: int = 50, temperature: float = 0.1) -> str:
        """Генерирует ответ с оптимизациями"""
        start_time = time.time()
        
        try:
            model = self.get_model()
            tokenizer = self.get_tokenizer()
            
            # Токенизируем промпт
            inputs = tokenizer(prompt, return_tensors="pt").to(self.device_config.device)
            
            # Максимально оптимизированные параметры для скорости
            generation_config = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.7,  # Еще больше уменьшаем
                "repetition_penalty": 1.0,  # Отключаем
                "do_sample": False,  # Используем greedy decoding
                "pad_token_id": tokenizer.pad_token_id,
                "eos_token_id": tokenizer.eos_token_id,
                "use_cache": True,
                "num_beams": 1,  # Greedy search
                "length_penalty": 1.0
            }
            
            # Дополнительные оптимизации для MPS
            if self.device_config.device == "mps":
                generation_config["use_cache"] = True
            
            # Генерируем ответ
            with torch.no_grad():
                outputs = model.generate(**inputs, **generation_config)
            
            # Декодируем ответ
            response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Извлекаем только новую часть ответа
            prompt_length = len(tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True))
            result = response_text[prompt_length:].strip()
            
            generation_time = time.time() - start_time
            logger.performance("Text generation", generation_time, 
                            max_tokens=max_tokens, device=self.device_config.device)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def get_device_info(self) -> Dict[str, Any]:
        """Возвращает информацию об устройстве"""
        return self.device_manager.get_device_info()
    
    def cleanup(self):
        """Очищает ресурсы"""
        logger.info("Cleaning up model resources")
        if self._model is not None:
            del self._model
            self._model = None
        
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        logger.info("Model cleanup completed") 