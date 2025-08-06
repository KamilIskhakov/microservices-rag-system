"""
Базовый класс скрапера
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import aiohttp
from bs4 import BeautifulSoup


class BaseScraper(ABC):
    """Базовый класс для всех скраперов"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.get('timeout', 30)),
            headers={
                'User-Agent': self.config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def scrape_page(self, url: str) -> Dict[str, Any]:
        """Скрапить одну страницу"""
        pass
    
    @abstractmethod
    async def parse_content(self, html: str) -> List[Dict[str, Any]]:
        """Парсить содержимое HTML"""
        pass
    
    @abstractmethod
    async def get_next_page_url(self, html: str, current_url: str) -> Optional[str]:
        """Получить URL следующей страницы"""
        pass
    
    async def scrape_with_pagination(self, start_url: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """Скрапить с пагинацией"""
        if not self.session:
            raise RuntimeError("Скрапер не инициализирован. Используйте async with.")
        
        all_data = []
        current_url = start_url
        page_count = 0
        
        try:
            while current_url and page_count < max_pages:
                self.logger.info(f"🔄 Скрапинг страницы {page_count + 1}: {current_url}")
                
                # Скрапим страницу
                page_data = await self.scrape_page(current_url)
                
                if page_data.get('success'):
                    content = page_data.get('content', '')
                    parsed_items = await self.parse_content(content)
                    all_data.extend(parsed_items)
                    
                    self.logger.info(f"✅ Найдено {len(parsed_items)} элементов на странице {page_count + 1}")
                    
                    # Получаем следующую страницу
                    current_url = await self.get_next_page_url(content, current_url)
                    page_count += 1
                    
                    # Задержка между запросами
                    if current_url:
                        delay = self.config.get('delay', 1.0)
                        await asyncio.sleep(delay)
                else:
                    self.logger.error(f"❌ Ошибка скрапинга страницы: {page_data.get('error')}")
                    break
            
            self.logger.info(f"✅ Скрапинг завершен. Всего страниц: {page_count}, элементов: {len(all_data)}")
            return all_data
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка скрапинга: {e}")
            return all_data
    
    async def make_request(self, url: str) -> Dict[str, Any]:
        """Выполнить HTTP запрос"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return {
                        'success': True,
                        'content': content,
                        'status_code': response.status,
                        'url': url
                    }
                else:
                    return {
                        'success': False,
                        'error': f"HTTP {response.status}",
                        'status_code': response.status,
                        'url': url
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def log_scraping_stats(self, total_items: int, total_pages: int, duration: float):
        """Логировать статистику скрапинга"""
        self.logger.info(f"📊 Статистика скрапинга:")
        self.logger.info(f"   Страниц обработано: {total_pages}")
        self.logger.info(f"   Элементов найдено: {total_items}")
        self.logger.info(f"   Время выполнения: {duration:.2f}с")
        self.logger.info(f"   Скорость: {total_items/duration:.2f} элементов/сек") 