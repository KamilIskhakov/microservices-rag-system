"""
Парсер для сайта Минюста РФ - Федеральный список экстремистских материалов
"""
import requests
from bs4 import BeautifulSoup
import time
import logging
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.domain.entities.scraped_data import ScrapedData
from config import scraper_settings

# Отключаем предупреждения о SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class MinjustScraper:
    def __init__(self):
        # URL сайта Минюста с экстремистскими материалами
        self.base_url = scraper_settings.MINJUST_BASE_URL
        self.session = requests.Session()
        
        # Настройка повторных попыток
        retry_strategy = Retry(
            total=scraper_settings.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': scraper_settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        # Отключаем проверку SSL для правительственных сайтов
        self.session.verify = False

    def fetch_page(self, page=1, max_retries=None):
        """Получает HTML страницы с экстремистскими материалами с повторными попытками"""
        if max_retries is None:
            max_retries = scraper_settings.MAX_RETRIES
            
        for attempt in range(max_retries):
            try:
                # Правильный URL для реестра экстремистских материалов
                url = f"{self.base_url}?page={page}"
                logger.info(f"Fetching page {page} from {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=scraper_settings.REQUEST_TIMEOUT, verify=False)
                
                if response.status_code == 404:
                    logger.warning(f"Page {page} not found (404)")
                    return None
                
                response.raise_for_status()
                logger.info(f"Successfully fetched page {page}, content length: {len(response.text)}")
                return response.text
                
            except requests.RequestException as e:
                logger.error(f"Error fetching page {page} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # Увеличиваем время ожидания
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch page {page} after {max_retries} attempts")
                    return None
        
        return None

    def parse(self, html):
        """Парсит HTML и извлекает информацию о материалах"""
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        items = []
        
        # Ищем основную таблицу с данными
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # Пропускаем заголовки и обрабатываем строки с данными
            for row_idx, row in enumerate(rows):
                # Пропускаем первую строку (заголовок)
                if row_idx == 0:
                    continue
                    
                cols = row.find_all(['td', 'th'])
                
                if len(cols) >= 2:  # Минимум номер и описание
                    # Извлекаем данные из колонок
                    number = cols[0].get_text(strip=True) if cols[0] else ""
                    description = cols[1].get_text(strip=True) if cols[1] else ""
                    date = cols[2].get_text(strip=True) if len(cols) > 2 and cols[2] else ""
                    
                    # Проверяем, что описание не пустое и содержательное
                    if description and len(description) > 10:
                        item = {
                            'number': number,
                            'description': description,
                            'date': date,
                            'full_text': f"№{number} {description} {date}".strip()
                        }
                        items.append(item)
        
        # Если ничего не найдено в таблицах, попробуем другие селекторы
        if not items:
            # Попробуем найти элементы списка
            list_items = soup.find_all(['li', 'div'], class_=lambda x: x and ('item' in x or 'entry' in x or 'material' in x))
            
            for item_element in list_items:
                text = item_element.get_text(strip=True)
                if text and len(text) > 20:  # Фильтруем короткие строки
                    item = {
                        'number': '',
                        'description': text,
                        'date': '',
                        'full_text': text
                    }
                    items.append(item)
        
        logger.info(f"Parsed {len(items)} items from HTML")
        return items

    def scrape_all(self, max_pages=None):
        """Скрапит все доступные страницы до конца"""
        page = 1
        all_items = []
        consecutive_empty_pages = 0
        max_empty_pages = 5  # Увеличиваем количество пустых страниц для надежности
        
        logger.info(f"Starting to scrape from {self.base_url}")
        
        while True:
            # Проверяем ограничение по страницам, если указано
            if max_pages and page > max_pages:
                logger.info(f"Reached max pages limit: {max_pages}")
                break
                
            logger.info(f"Scraping page {page}")
            
            html = self.fetch_page(page)
            if html is None:
                consecutive_empty_pages += 1
                logger.info(f"Page {page} returned None, consecutive empty pages: {consecutive_empty_pages}")
                if consecutive_empty_pages >= max_empty_pages:
                    logger.info(f"Stopping after {consecutive_empty_pages} consecutive empty pages")
                    break
                page += 1
                continue
            
            items = self.parse(html)
            if not items:
                consecutive_empty_pages += 1
                logger.info(f"Page {page} has no items, consecutive empty pages: {consecutive_empty_pages}")
                if consecutive_empty_pages >= max_empty_pages:
                    logger.info(f"Stopping after {consecutive_empty_pages} consecutive pages with no items")
                    break
            else:
                consecutive_empty_pages = 0
                all_items.extend(items)
                logger.info(f"Page {page}: found {len(items)} items, total: {len(all_items)}")
            
            page += 1
            time.sleep(scraper_settings.DELAY_BETWEEN_REQUESTS)  # Используем настройку задержки
        
        logger.info(f"Scraping completed. Total items: {len(all_items)} from {page-1} pages")
        return all_items

    def scrape_to_scraped_data(self, max_pages=None) -> List[ScrapedData]:
        """Скрапит данные и преобразует в объекты ScrapedData"""
        # Используем настройку MAX_PAGES если не указано иное
        if max_pages is None and scraper_settings.MAX_PAGES:
            max_pages = scraper_settings.MAX_PAGES
            
        raw_items = self.scrape_all(max_pages)
        scraped_data = []
        
        for item in raw_items:
            try:
                # Парсим дату
                court_date = self.parse_date(item.get('date', ''))
                
                # Создаем объект ScrapedData с приведением к нижнему регистру
                material = ScrapedData(
                    id=None,
                    number=item.get('number', '').lower(),
                    content=item.get('description', '').lower(),
                    date=court_date,
                    source="minjust"
                )
                
                scraped_data.append(material)
                
            except Exception as e:
                logger.warning(f"Ошибка создания ScrapedData для элемента: {e}")
                continue
        
        logger.info(f"Преобразовано {len(scraped_data)} материалов в ScrapedData")
        return scraped_data

    def parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из строки"""
        try:
            if not date_str or date_str.strip() == '':
                return datetime.now()
            
            # Убираем лишние символы
            date_str = date_str.strip()
            
            # Пробуем разные форматы даты
            formats = [
                '%d.%m.%Y',
                '%d.%m.%y',
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d.%m.%Y %H:%M',
                '%d.%m.%Y %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Если не удалось распарсить, возвращаем текущую дату
            logger.warning(f"Не удалось распарсить дату: {date_str}")
            return datetime.now()
            
        except Exception as e:
            logger.error(f"Ошибка парсинга даты '{date_str}': {e}")
            return datetime.now() 