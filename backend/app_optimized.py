from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from api.check import router as check_router
from api.update import router as update_router
from services.rag_service import RAGService
from services.database_updater import DatabaseUpdater
from services.scheduler import TaskScheduler
from services.logger import logger
from config import settings
from middleware.security import security_middleware
import asyncio
import multiprocessing
import uvicorn

app = FastAPI(
    title="Extremist Material Checker API (Optimized)",
    # Отключаем документацию для безопасности
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Подключаем роутеры
app.include_router(check_router, prefix="/api/v1")
app.include_router(update_router, prefix="/api/v1")

# Глобальные экземпляры сервисов
rag_service: RAGService = None
database_updater: DatabaseUpdater = None
scheduler: TaskScheduler = None

# Оптимизированные настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все origins для разработки
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Cache-Control", "Pragma", "Expires"]
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Добавляет заголовки безопасности ко всем ответам"""
    response = await call_next(request)
    security_middleware.add_security_headers(response)
    return response

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске сервера"""
    global rag_service, database_updater, scheduler
    
    logger.info("Starting up Optimized Extremist Material Checker API...")
    
    try:
        # Инициализируем RAG сервис при запуске
        rag_service = RAGService()
        
        # Проверяем базу данных
        await check_database()
        
        # Инициализируем обновлятель БД
        database_updater = DatabaseUpdater(rag_service)
        
        # Инициализируем планировщик задач
        scheduler = TaskScheduler()
        scheduler.add_database_update_task(database_updater, interval_hours=24)
        
        # Запускаем планировщик в фоновом режиме
        asyncio.create_task(scheduler.start())
        
        logger.info("Optimized API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

async def check_database():
    """Проверяет работоспособность базы данных"""
    try:
        # Проверяем векторное хранилище
        vector_store = rag_service.vector_store
        
        if not vector_store.texts:
            logger.warning("Vector database is empty!")
            raise Exception("База данных пустая. Необходимо загрузить данные.")
        
        logger.info(f"Database check passed. Found {len(vector_store.texts)} documents")
        
        # Проверяем, что модель может быть загружена (не проверяем сам объект модели)
        try:
            # Пробуем получить токенизатор - это проверит доступность модели
            tokenizer = rag_service.model_manager.get_tokenizer()
            logger.info("Model accessibility check passed")
        except Exception as e:
            logger.error(f"Model accessibility check failed: {e}")
            raise Exception(f"Ошибка доступа к модели: {e}")
        
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при выключении сервера"""
    global scheduler
    
    logger.info("Shutting down Optimized API...")
    
    if scheduler:
        await scheduler.stop()
    
    if rag_service:
        rag_service.cleanup()
    
    logger.info("Optimized API shutdown completed")

@app.options("/check")
async def check_options_global(request: Request, response: Response):
    """Обработка OPTIONS запросов для /check"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Extremist Material Checker API (Optimized)",
        "version": "2.0.0",
        "status": "running",
        "optimizations": [
            "multiprocessing",
            "async_processing", 
            "caching",
            "load_balancing"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "process_id": multiprocessing.current_process().pid
    }

# Конфигурация для высоких нагрузок
if __name__ == "__main__":
    # Определяем количество воркеров на основе CPU
    cpu_count = multiprocessing.cpu_count()
    workers = cpu_count * 2 + 1
    
    logger.info(f"Starting optimized server with {workers} workers on {cpu_count} CPU cores")
    
    # Запускаем с оптимизациями
    uvicorn.run(
        "app_optimized:app",
        host="0.0.0.0",
        port=8000,
        workers=workers,
        loop="uvloop",  # Используем uvloop для лучшей производительности
        http="httptools",  # Используем httptools для быстрого парсинга
        access_log=True,
        log_level="info"
    ) 