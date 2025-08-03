import requests
from bs4 import BeautifulSoup
from config import settings
import time
import logging
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Отключаем предупреждения о SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class MinjustScraper:
    def __init__(self):
        self.base_url = settings.MINJUST_BASE_URL
        self.session = requests.Session()
        
        # Настройка повторных попыток
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        # Отключаем проверку SSL для правительственных сайтов
        self.session.verify = False

    def fetch_page(self, page=1, max_retries=3):
        """Получает HTML страницы с экстремистскими материалами с повторными попытками"""
        for attempt in range(max_retries):
            try:
                # Правильный URL для реестра экстремистских материалов
                url = f"{self.base_url}?page={page}"
                logger.info(f"Fetching page {page} from {url} (attempt {attempt + 1})")
                
                response = self.session.get(url, timeout=60, verify=False)
                
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
            time.sleep(1)  # Добавляем задержку между запросами
        
        logger.info(f"Scraping completed. Total items: {len(all_items)} from {page-1} pages")
        return all_items