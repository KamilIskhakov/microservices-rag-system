"""
Конфигурация для скраппера
"""
import os
from typing import Optional

class ScraperSettings:
    """Настройки скраппера"""
    
    # URL сайта Минюста
    MINJUST_BASE_URL: str = os.getenv("MINJUST_BASE_URL", "https://minjust.gov.ru/ru/extremist-materials/")
    
    # Настройки парсинга
    MAX_PAGES: Optional[int] = int(os.getenv("MAX_PAGES", "2")) if os.getenv("MAX_PAGES") else 2
    DELAY_BETWEEN_REQUESTS: float = float(os.getenv("DELAY_BETWEEN_REQUESTS", "0.1"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    
    # Настройки User-Agent
    USER_AGENT: str = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Настройки RAG интеграции
    VECTORSTORE_URL: str = os.getenv("VECTORSTORE_URL", "http://vectorstore:8002")
    RAG_INTEGRATION_ENABLED: bool = os.getenv("RAG_INTEGRATION_ENABLED", "true").lower() == "true"

# Глобальный экземпляр настроек
scraper_settings = ScraperSettings() 