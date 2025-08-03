import os
from pydantic_settings import BaseSettings
from typing import Optional
        
class Settings(BaseSettings):
    # Основные настройки
    QWEN_MODEL_PATH: str = "models/qwen-model"
    VECTOR_STORE_PATH: str = "data/index.faiss"
    VECTOR_DIM: int = 384
    FAISS_INDEX_PATH: str = "data/index.faiss"
    FAISS_META_PATH: str = "data/index.faiss.meta"
    
    # Настройки безопасности
    RATE_LIMIT_PER_MINUTE: int = 60
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "chrome-extension://*"]
    
    # Настройки логирования
    LOG_LEVEL: str = "INFO"
    LOG_SENSITIVE_DATA: bool = False
    
    # Настройки HTTPS
    USE_HTTPS: bool = False
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()