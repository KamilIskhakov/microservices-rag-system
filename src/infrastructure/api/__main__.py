"""
Точка входа для AI Model API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import uvicorn
import logging
from src.infrastructure.api.ai_model_api import app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🚀 Запуск AI Model API")
    
    # Запускаем с оптимизациями
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=8003,
        workers=1,  # Один воркер для загрузки модели
        loop="uvloop",  # Используем uvloop для лучшей производительности
        http="httptools",  # Используем httptools для быстрого парсинга
        access_log=True,
        log_level="info"
    ) 