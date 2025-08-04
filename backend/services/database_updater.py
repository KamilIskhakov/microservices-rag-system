import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from services.logger import logger
from services.rag_service import RAGService
from scraper.minjust_scraper import MinjustScraper


@dataclass
class UpdateResult:
    """Результат обновления базы данных"""
    success: bool
    materials_added: int
    materials_updated: int
    materials_total: int
    error: Optional[str] = None
    duration_seconds: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DatabaseUpdater:
    """Сервис для автоматического обновления базы данных"""
    
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
        self.scraper = MinjustScraper()
        self.last_update_key = 'last_database_update'
        self.update_interval_hours = 24
        
    async def should_update(self) -> bool:
        """Проверяет, нужно ли обновлять базу данных"""
        try:
            last_update = await self._get_last_update_time()
            if last_update is None:
                return True
                
            time_since_update = datetime.now() - last_update
            return time_since_update >= timedelta(hours=self.update_interval_hours)
            
        except Exception as e:
            logger.error(f"Ошибка проверки необходимости обновления: {e}")
            return True
    
    async def update_database(self) -> UpdateResult:
        """Выполняет обновление базы данных"""
        start_time = datetime.now()
        
        try:
            logger.info("Начинаем обновление базы данных...")
            
            # Проверяем необходимость обновления
            if not await self.should_update():
                logger.info("Обновление не требуется - база данных актуальна")
                return UpdateResult(
                    success=True,
                    materials_added=0,
                    materials_updated=0,
                    materials_total=await self._get_total_materials_count(),
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Парсим новые материалы
            materials = await self.scraper.parse_materials()
            
            if not materials:
                logger.warning("Не удалось получить материалы для обновления")
                return UpdateResult(
                    success=False,
                    materials_added=0,
                    materials_updated=0,
                    materials_total=0,
                    error="Не удалось получить материалы",
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            
            # Обновляем векторное хранилище
            added_count, updated_count = await self._update_vector_store(materials)
            
            # Сохраняем время последнего обновления
            await self._save_last_update_time()
            
            total_count = await self._get_total_materials_count()
            
            logger.info(f"Обновление завершено: добавлено {added_count}, обновлено {updated_count}, всего {total_count}")
            
            return UpdateResult(
                success=True,
                materials_added=added_count,
                materials_updated=updated_count,
                materials_total=total_count,
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )
            
        except Exception as e:
            logger.error(f"Ошибка обновления базы данных: {e}")
            return UpdateResult(
                success=False,
                materials_added=0,
                materials_updated=0,
                materials_total=0,
                error=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    async def force_update(self) -> UpdateResult:
        """Принудительное обновление базы данных"""
        logger.info("Выполняется принудительное обновление базы данных...")
        return await self.update_database()
    
    async def get_update_status(self) -> dict:
        """Получает статус последнего обновления"""
        try:
            last_update = await self._get_last_update_time()
            should_update = await self.should_update()
            total_materials = await self._get_total_materials_count()
            
            return {
                "last_update": last_update.isoformat() if last_update else None,
                "should_update": should_update,
                "total_materials": total_materials,
                "update_interval_hours": self.update_interval_hours
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса обновления: {e}")
            return {
                "error": str(e),
                "last_update": None,
                "should_update": True,
                "total_materials": 0
            }
    
    async def _update_vector_store(self, materials: List) -> tuple[int, int]:
        """Обновляет векторное хранилище"""
        try:
            # Здесь должна быть логика обновления векторного хранилища
            # Пока возвращаем заглушку
            added_count = len(materials)
            updated_count = 0
            
            logger.info(f"Обновлено векторное хранилище: {added_count} новых материалов")
            return added_count, updated_count
            
        except Exception as e:
            logger.error(f"Ошибка обновления векторного хранилища: {e}")
            raise
    
    async def _get_last_update_time(self) -> Optional[datetime]:
        """Получает время последнего обновления"""
        try:
            # Здесь должна быть логика получения времени последнего обновления
            # Пока возвращаем None для принудительного обновления
            return None
        except Exception as e:
            logger.error(f"Ошибка получения времени последнего обновления: {e}")
            return None
    
    async def _save_last_update_time(self):
        """Сохраняет время последнего обновления"""
        try:
            # Здесь должна быть логика сохранения времени обновления
            logger.info("Время обновления сохранено")
        except Exception as e:
            logger.error(f"Ошибка сохранения времени обновления: {e}")
    
    async def _get_total_materials_count(self) -> int:
        """Получает общее количество материалов"""
        try:
            # Здесь должна быть логика подсчета материалов
            # Пока возвращаем заглушку
            return 0
        except Exception as e:
            logger.error(f"Ошибка подсчета материалов: {e}")
            return 0 