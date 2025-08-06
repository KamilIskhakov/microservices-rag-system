"""
Конфигурация переменных окружения для продакшена
"""
import os
from typing import Optional


class EnvironmentConfig:
    """Конфигурация переменных окружения"""
    
    # Модели
    MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/qwen-model_full")
    MODEL_NAME = os.getenv("MODEL_NAME", "qwen-model_full")
    MODEL_TYPE = os.getenv("MODEL_TYPE", "causal_lm")
    
    # Устройства
    DEVICE_TYPE = os.getenv("DEVICE_TYPE", "auto")  # auto, cpu, gpu
    CPU_THREADS = int(os.getenv("CPU_THREADS", "4"))
    GPU_MEMORY_FRACTION = float(os.getenv("GPU_MEMORY_FRACTION", "0.8"))
    
    # Сервисы
    AI_MODEL_URL = os.getenv("AI_MODEL_URL", "http://ai-model-optimized:8003")
    VECTORSTORE_URL = os.getenv("VECTORSTORE_URL", "http://vectorstore:8002")
    REQUEST_PROCESSOR_URL = os.getenv("REQUEST_PROCESSOR_URL", "http://request-processor-optimized:8004")
    API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway-optimized:8000")
    SCRAPER_URL = os.getenv("SCRAPER_URL", "http://scraper-optimized:8001")
    PAYMENT_URL = os.getenv("PAYMENT_URL", "http://payment-optimized:8005")
    
    # Scraper
    MINJUST_URL = os.getenv("MINJUST_URL", "http://minjust.ru")
    SCRAPER_DELAY = float(os.getenv("SCRAPER_DELAY", "0.1"))
    SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "10"))
    SCRAPER_MAX_PAGES = int(os.getenv("SCRAPER_MAX_PAGES", "2"))
    
    # Производительность
    MAX_GENERATION_TIME = int(os.getenv("MAX_GENERATION_TIME", "30"))
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "8"))
    MAX_PROCESSES = int(os.getenv("MAX_PROCESSES", "2"))
    MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "10"))
    GENERATION_TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", "0.1"))
    
    # Память
    MAX_MEMORY_USAGE = float(os.getenv("MAX_MEMORY_USAGE", "0.9"))
    MIN_MEMORY_GB = int(os.getenv("MIN_MEMORY_GB", "2"))
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis-optimized:6379")
    
    # Логирование
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Безопасность
    API_KEY = os.getenv("API_KEY", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Мониторинг
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT = int(os.getenv("METRICS_PORT", "9090")) 